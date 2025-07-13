from datetime import datetime, timezone
import logging
import time
from typing import List
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.platform.BasePlatform import BasePlatform
from backend.models.PlatformType import PlatformType
from backend.models.Order import Order
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
    
    def place_order(self, order: Order) -> dict:
        
        data = {
            "ticker": order.market_id,
            "action": order.action,
            "type": order.order_type,
            "side": order.side,
            "count": order.size,
            "client_order_id": order.client_order_id
        }

        if order.order_type == 'limit':
            if order.price is None:
                raise ValueError("Price must be provided for limit orders.")
            if order.side == 'yes':
                data["yes_price"] = order.price
            else:
                data["no_price"] = order.price
        elif order.order_type == 'market':
            if order.action == 'buy':
                if order.max_price is None:
                    raise ValueError("A maximum cost (max_price) must be provided for market buy orders.")
                data["buy_max_cost"] = order.max_price * order.size
            elif order.action == 'sell':
                # For market sells, no price information is needed, so we do nothing.
                pass

        try:
            response = self.session.post(f"{self.base_url}/portfolio/orders", json=data)
            response.raise_for_status()
            if response.status_code == 201:
                order_data = response.json()
                order.id = order_data['order']['order_id']
                return order_data
        except requests.exceptions.HTTPError as err:
            print(f"Error placing order. Response from server: {err.response.text}")
            raise err


    def cancel_order(self, order: Order):
        if not order.id:
            raise ValueError("Order ID is not set. Cannot cancel order.")
        
        try:
            response = self.session.delete(f"{self.base_url}/portfolio/orders/{order.id}")
            response.raise_for_status()
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"Error cancelling order. Response from server: {err.response.text}")
            raise err

