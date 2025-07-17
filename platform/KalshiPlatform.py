from datetime import datetime, timezone
import logging
import time
from typing import List
from models.Market import Market
from models.Orderbook import Orderbook
from platform.BasePlatform import BasePlatform
from models.PlatformType import PlatformType
from models.Order import Order
import requests
from dotenv import load_dotenv
import asyncio
import time
import httpx
import os
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from requests.auth import AuthBase
from urllib.parse import urlparse
from models.OrderStatus import OrderStatus

load_dotenv()  

class KalshiAuth(AuthBase):
    def __init__(self, key_id: str, private_key: rsa.RSAPrivateKey):
        self.key_id = key_id
        self.private_key = private_key

    def __call__(self, r):
        timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
        parsed_url = urlparse(r.url)
        path = parsed_url.path
        if parsed_url.query:
            path += "?" + parsed_url.query
        
        msg_string = f"{timestamp}{r.method.upper()}{path}"

        signature = self.private_key.sign(
            msg_string.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        r.headers['KALSHI-ACCESS-KEY'] = self.key_id
        r.headers['KALSHI-ACCESS-TIMESTAMP'] = timestamp
        r.headers['KALSHI-ACCESS-SIGNATURE'] = encoded_signature
        
        if 'Authorization' in r.headers:
            del r.headers['Authorization']
        if 'Content-Type' not in r.headers:
            r.headers['Content-Type'] = 'application/json'
            
        return r

class KalshiHttpxAuth(httpx.Auth):
    def __init__(self, key_id: str, private_key: rsa.RSAPrivateKey):
        self.key_id = key_id
        self.private_key = private_key

    def auth_flow(self, r):
        timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))
        path = r.url.path
        if r.url.query:
            path += "?" + r.url.query.decode('utf-8')

        msg_string = f"{timestamp}{r.method.upper()}{path}"
        
        signature = self.private_key.sign(
            msg_string.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        r.headers['KALSHI-ACCESS-KEY'] = self.key_id
        r.headers['KALSHI-ACCESS-TIMESTAMP'] = timestamp
        r.headers['KALSHI-ACCESS-SIGNATURE'] = encoded_signature
        
        if 'Authorization' in r.headers:
            del r.headers['Authorization']
        if 'Content-Type' not in r.headers:
            r.headers['Content-Type'] = 'application/json'

        yield r
        
class KalshiPlatform(BasePlatform):
    """
    Kalshi Platform implementation that interfaces with the Kalshi API.

    Kalshi is a prediction market platform that allows users to trade on
    the outcome of real-world events.
    """
    
    def __init__(self):
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = requests.Session()

        key_id = os.getenv("KALSHI_ACCESS_KEY")
        private_key_pem = os.getenv("KALSHI_PRIVATE_KEY")

        if not key_id or not private_key_pem:
            raise ValueError("KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY environment variables must be set.")
        
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        self.key_id = key_id

        self.session.auth = KalshiAuth(self.key_id, self.private_key)

        logging.getLogger("httpx").setLevel(logging.WARNING)

    async def _get_order_books_async(self, market_ids: List[str], markets: dict) -> List[Orderbook]:
        auth = KalshiHttpxAuth(self.key_id, self.private_key)
        async with httpx.AsyncClient(auth=auth) as session:
            tasks = [
                self._fetch_orderbook(session, self.base_url, mid, markets)
                for mid in market_ids
            ]
            results = await asyncio.gather(*tasks)
            return [ob for ob in results if ob is not None]

    async def _fetch_orderbook(self, session, base_url, market_id, markets):
        try:
            response = await session.get(f"{base_url}/markets/{market_id}/orderbook")
            if response.status_code != 200:
                return None

            data = response.json()["orderbook"]
            data2 = markets[market_id]
            highest_no_bid = data2["no_bid"]
            highest_yes_bid = data2["yes_bid"]

            yes_bids = []
            yes_asks = []
            no_bids = []
            no_asks = []

            yes = data.get("yes") or []
            no = data.get("no") or []
            for a_yes in yes:
                if a_yes[0] <= highest_yes_bid:
                    yes_bids.append([a_yes[0] * 10, a_yes[1] * 100])

            for a_no in no:
                if a_no[0] <= highest_no_bid:
                    no_bids.append([a_no[0] * 10, a_no[1] * 100])

            for i in range(len(yes_bids)):
                no_asks.append([1000 - yes_bids[i][0], yes_bids[i][1]])
            for i in range(len(no_bids)):
                yes_asks.append([1000 - no_bids[i][0], no_bids[i][1]])


            yes_bids.sort(key=lambda x: x[0])
            yes_asks.sort(key=lambda x: x[0])
            no_bids.sort(key=lambda x: x[0])
            no_asks.sort(key=lambda x: x[0])
            return Orderbook(
                market_id=market_id,
                timestamp=int(time.time() * 1000),
                yes={"bid": yes_bids, "ask": yes_asks},
                no={"bid": no_bids, "ask": no_asks}
            )
        except Exception as e:
            print(f"Error processing market {market_id}: {e}")
            return None


    def get_order_books(self, market_ids: List[str]) -> List[Orderbook]:
        
        """
        Get order books for the specified market IDs.
        
        Args:
            market_ids: List of market IDs to get order books for
            
        Returns:
            List of Orderbook objects containing bid/ask data
        """

        markets = {}
        while len(markets) < len(market_ids):
            limited_request_ids = market_ids[len(markets):len(markets) + 50]
            response = self.session.get(f"{self.base_url}/markets?tickers={','.join(limited_request_ids)}")
            if response.status_code == 200:
                data = response.json()["markets"]
                for a_market in data:
                    markets[a_market['ticker']] = a_market
    
        return asyncio.run(self._get_order_books_async(market_ids, markets))

    def find_new_markets(self, num_markets: int) -> List[str]:
        """
        Find new markets from Kalshi API.
        
        Args:
            num_markets: Number of markets to return
            
        Returns:
            List of market IDs for new/active markets
        """

        if num_markets <= 0:
            return []
        curr_num_markets = 0
        market_ids = []
        cursor = ""
        while curr_num_markets < num_markets:
            num_pages_to_fetch = min((num_markets - curr_num_markets), 1000)
            response = self.session.get(f"{self.base_url}/markets?limit={num_pages_to_fetch}&cursor={cursor}&status=open")

            parsed_response = response.json()

            for market in parsed_response['markets']:
                market_ids.append(market['ticker'])
                curr_num_markets += 1
                if curr_num_markets >= num_markets:
                    break
            cursor = parsed_response.get('cursor')

        return market_ids
    

    def get_markets(self, market_ids: List[str]) -> List[Market]:

        """
        Get market details for the specified market IDs.
        
        Args:
            market_ids: List of market IDs to get details for
            
        Returns:
            List of Market objects with market information
        """
        if not market_ids:
            return []

        markets = []
        while len(markets) < len(market_ids):
            limited_request_ids = market_ids[len(markets):len(markets) + 50]
            response = self.session.get(f"{self.base_url}/markets?tickers={','.join(limited_request_ids)}")
            if response.status_code == 200:
                data = response.json()["markets"]
                for a_market in data:
                    close_iso_time = a_market["close_time"]
                    dt = datetime.strptime(close_iso_time, "%Y-%m-%dT%H:%M:%SZ")
                    unix_ts = int(dt.timestamp())

                    market = Market(
                        platform=PlatformType.KALSHI,
                        market_id=a_market['ticker'],
                        name=a_market['title'],
                        rules=a_market['rules_primary'],
                        close_timestamp=unix_ts
                    )
                    markets.append(market)
        return markets

    def place_order(self, order: Order) -> None:
        """
        Place an order on the Kalshi platform.
        """
        response = self.session.post(
            f"{self.base_url}/portfolio/orders",
            json={
                "ticker": order.market_id,
                "action": order.action,
                "type": order.order_type,
                "count": order.size,
                "yes_price": order.price,
                "buy_max_cost": order.max_price,
                "side": order.side,
                "tif": order.time_in_force,
                "client_order_id": order.client_order_id,
            }
        )

        if response.status_code == 201:
            response_json = response.json()
            order_data = response_json.get("order", {})
            order.order_id = order_data.get("order_id")
            order.status = OrderStatus.OPEN
            logging.info(f"Order placed successfully: {order.order_id}")
        else:
            order.status = OrderStatus.FAILED
            logging.error(f"Failed to place order: {response.status_code} - {response.text}")

    def cancel_order(self, order: Order) -> None:
        """
        Cancel a specific order on the Kalshi platform.
        """
        if not order.order_id:
            logging.error("Cannot cancel Kalshi order: order_id is not set.")
            return

        # Per Kalshi docs, this reduces the resting contracts to zero.
        response = self.session.delete(f"{self.base_url}/portfolio/orders/{order.order_id}")

        if response.status_code == 200:
            logging.info(f"Order {order.order_id} cancelled successfully on Kalshi.")
            order.status = OrderStatus.CANCELED
        else:
            logging.error(f"Failed to cancel Kalshi order {order.order_id}: {response.status_code} - {response.text}")

    def get_order_status(self, order: Order) -> None:
        """
        Get the status of a specific order from the Kalshi platform and update the order object.
        """
        if not order.order_id:
            logging.error("Cannot get order status: order_id is not set.")
            order.status = OrderStatus.FAILED
            return

        response = self.session.get(f"{self.base_url}/portfolio/orders/{order.order_id}")

        if response.status_code != 200:
            logging.error(f"Failed to get order status for {order.order_id}: {response.status_code} - {response.text}")
            # Decide if status should be set to FAILED or left as is
            return

        order_data = response.json().get("order", {})
        
        kalshi_status = order_data.get("status")
        
        status_map = {
            "resting": OrderStatus.OPEN,
            "executed": OrderStatus.EXECUTED,
            "canceled": OrderStatus.CANCELED,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
        }
        
        order.status = status_map.get(kalshi_status, order.status)
        order.fill_size = order_data.get("fillsTotalCount", order.fill_size)

        logging.info(f"Updated order {order.order_id} status to {order.status.value}")
        