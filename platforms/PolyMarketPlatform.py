from typing import List
from models.Market import Market
from models.Orderbook import Orderbook
from platforms.BasePlatform import BasePlatform
from models.Order import Order
from py_clob_client.client import ClobClient 
from py_clob_client.clob_types import BookParams, OrderArgs, OrderType
from dotenv import load_dotenv
import os
import requests
from models.PlatformType import PlatformType
import logging
import json
import aiohttp
import asyncio
from datetime import datetime
import time
from py_clob_client.order_builder.constants import BUY, SELL
from models.OrderStatus import OrderStatus
from models.Trade import Trade
from web3 import Web3

load_dotenv()  
class PolyMarketPlatform(BasePlatform):
    """
    PolyMarket Platform implementation that interfaces with the PolyMarket GraphQL API.
    
    PolyMarket is a prediction market platform that allows users to trade on
    the outcome of real-world events.
    """
    
    def __init__(self):
        # for CLOB client access
        host: str = "https://clob.polymarket.com"
        key: str = os.getenv("PRIVATE_KEY")
        POLYMARKET_PROXY_ADDRESS : str = os.getenv("PROXY_ADDRESS")
        chain_id: int = 137
        # Using signature_type=1, which corresponds to an Email/Magic link account (like Google sign-in)
        self.client = ClobClient(host, key=key, chain_id=chain_id, signature_type=1, funder=POLYMARKET_PROXY_ADDRESS)

        # for Gamma API access
        self.base_url = "https://gamma-api.polymarket.com"
        self.client.set_api_creds(self.client.create_or_derive_api_creds())

    def get_balance(self) -> float:
        """
        Fetches the USDC balance of the user's proxy contract from the Polygon blockchain.
        This represents the funds "deposited" and available for trading on PolyMarket.
        """
        # Connect to the Polygon network
        w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com/"))

        balance_of_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
        usdc_contract_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        usdc_contract = w3.eth.contract(address=usdc_contract_address, abi=balance_of_abi)

        proxy_address = os.getenv("PROXY_ADDRESS")
        if not proxy_address:
            raise ValueError("PROXY_ADDRESS environment variable not set.")
        
        checksum_proxy_address = Web3.to_checksum_address(proxy_address)
        balance_wei = usdc_contract.functions.balanceOf(checksum_proxy_address).call()
        balance_usd = float(balance_wei / (10**6))
        
        return balance_usd

    def _get_trade(self, trade_id: str) -> dict:
        """Fetches a single trade by its ID."""
        response = requests.get(f"{self.client.host}/data/trade/{trade_id}")
        response.raise_for_status()
        return response.json()

    async def _fetch_market(self, session, base_url, market_id):
        url = f"{base_url}/markets?condition_ids={market_id}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return market_id, json.loads(data[0]["clobTokenIds"])

    async def _fetch_all_cid_to_tkd(self, base_url, market_ids):
        cid_to_tkd = {}
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self._fetch_market(session, base_url, market_id) for market_id in market_ids]
            results = await asyncio.gather(*tasks)
            for market_id, tkd_list in results:
                cid_to_tkd[market_id] = tkd_list
        return cid_to_tkd

    def get_order_books(self, market_ids: List[str]) -> List[Orderbook]:
        
        """
        Get order books for the specified market IDs.
        
        Args:
            market_ids: List of market IDs to get order books for
            
        Returns:
            List of Orderbook objects containing bid/ask data
        """

        market_id_set = set(market_ids)

        

        # str -> [str, str]
        cid_to_tkd = {}

        tkd_to_order_book = {}
        
        start_time = datetime.now()
        cid_to_tkd = asyncio.run(self._fetch_all_cid_to_tkd(self.base_url, market_id_set))

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        all_tkd = [tkd for tkd_list in cid_to_tkd.values() for tkd in tkd_list]

        
        def chunk_list(lst, size):
            for i in range(0, len(lst), size):
                yield lst[i:i + size]

        CHUNK_SIZE = 50
        params = [BookParams(token_id=t) for t in all_tkd]
        temp_tkd_to_orderbook = []

        for chunk in chunk_list(params, CHUNK_SIZE):

            partial_result = self.client.get_order_books(params=chunk)
            temp_tkd_to_orderbook.extend(partial_result)

        for i, tkd in enumerate(all_tkd):
            tkd_to_order_book[tkd] = temp_tkd_to_orderbook[i]
        orderbooks = []
        for market_id in market_ids:

            yes_token = cid_to_tkd[market_id][0]
            no_token = cid_to_tkd[market_id][1]

            yes_order_book = tkd_to_order_book[yes_token]
            no_order_book = tkd_to_order_book[no_token]
            yes_bid = []
            yes_ask = []
            
            # get yes bid
            for an_order_summary in yes_order_book.bids:
                yes_bid.append([int(float(an_order_summary.price) * 1000), int(float(an_order_summary.size) * 100)])

            # get yes ask
            for an_order_summary in yes_order_book.asks:
                yes_ask.append([int(float(an_order_summary.price) * 1000), int(float(an_order_summary.size) * 100)])

            
            no_bid = []
            no_ask = []
            # get no bid
            for an_order_summary in no_order_book.bids:
                no_bid.append([int(float(an_order_summary.price) * 1000), int(float(an_order_summary.size) * 100)])

            # get no ask
            for an_order_summary in no_order_book.asks:
                no_ask.append([int(float(an_order_summary.price) * 1000), int(float(an_order_summary.size) * 100)])
            
            yes_bid.sort(key=lambda x: x[0])
            yes_ask.sort(key=lambda x: x[0])
            no_bid.sort(key=lambda x: x[0])
            no_ask.sort(key=lambda x: x[0])

            orderbook = Orderbook(
                market_id=market_id,
                timestamp=int(time.time() * 1000),
                yes={
                "bid": yes_bid,
                "ask": yes_ask
                },
                no={
                    "bid": no_bid,
                    "ask": no_ask
                }
            )

            orderbooks.append(orderbook)

        return orderbooks

    def find_new_markets(self, num_markets: int) -> List[str]:
        """
        Find new markets from PolyMarket using GraphQL.
        
        Args:
            num_markets: Number of markets to return
            
        Returns:
            List of market IDs for new/active markets
        """

        num_requests = 0
        new_markets = set()
        page_offset = 0
        while num_requests < num_markets:
            # https://gamma-api.polymarket.com/markets?order=id&closed=false&active=true&ascending=false
            limit = 500 # max limit per request
            limit = min(limit, num_markets - num_requests)
            response = requests.request("GET", f"{self.base_url}/markets?order=id&closed=false&active=true&ascending=false&limit=500&offset={page_offset}")

            for a_market in response.json():
                if a_market.get("endDateIso") is not None and a_market["endDateIso"] is not None:
                    condition_id = a_market.get("conditionId")
                    if condition_id and condition_id not in new_markets:
                        new_markets.add(condition_id)
                        num_requests += 1
                        if num_requests >= num_markets:
                            break
            page_offset += 500
        return list(new_markets)

    def get_markets(self, market_ids: List[str]) -> List[Market]:
        """
        Get market details for the specified market IDs using the Gamma REST API.

        Args:
            market_ids: List of condition IDs (market IDs) to retrieve

        Returns:
            List of Market objects with market information
        """
        market_id_set = set(market_ids)
        print(f"Fetching markets for IDs: {market_id_set}")
        matched_markets = []

        offset = 0
        limit = 500
        seen_ids = set()
        

        while len(seen_ids) < len(market_id_set):
            url = f"{self.base_url}/markets?order=id&closed=false&active=true&ascending=false&limit={limit}&offset={offset}"
            response = requests.get(url)
            response.raise_for_status()

            markets = response.json()
            if not markets:
                break  # no more data
            for m in markets:
                cid = m.get("conditionId")
                if cid in market_id_set:
                
                    iso = m["endDate"]
                    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
                    unix_ts = int(dt.timestamp())

                    matched_markets.append(Market(
                        platform=PlatformType.POLYMARKET,
                        market_id=cid,
                        name=m["question"],
                        rules=m["description"],
                        close_timestamp=unix_ts
                    ))
                    seen_ids.add(cid)
            offset += 500
        return matched_markets

    def place_order(self, order: Order) -> None:
        if order.size < 5:
            logging.error(f"PolyMarket order failed: size ({order.size}) is less than the minimum of 5.")
            order.status = OrderStatus.FAILED
            return
            
        order_price = None

        if order.order_type == 'limit':
            order_price = order.price / 100  # Convert cents to dollars
        elif order.order_type == 'market':
            if order.action == 'buy':
                order_price = order.max_price / 100  # Convert cents to dollars
            else: # Market Sell
                order_price = 0.01 # Set aggressive floor price to simulate market sell

        if order_price is None:
            raise ValueError("Could not determine price for PolyMarket order.")

        token_id = self._get_token_id(order.market_id, order.side)
        
        order_action = BUY if order.action.lower() == 'buy' else SELL

        order_args = OrderArgs(
            price=order_price,
            size=float(order.size),
            side=order_action,
            token_id=token_id,
        )

        try:
            # Based on extensive testing, the py_clob_client library consistently
            # produces 'invalid signature' errors for non-GTC order types.
            # The server gives conflicting error messages regarding the 'expiration'
            # field, which is the likely root cause within the client library.
            # To ensure all orders can be placed, we are forcing them to GTC,
            # which is the only type that signs reliably.
            signed_order = self.client.create_order(order_args)
            order_receipt = self.client.post_order(signed_order, OrderType.GTC) # Force GTC
            order.order_id = order_receipt["orderID"]
            order.status = OrderStatus.OPEN
            logging.info(f"PolyMarket order placed successfully: {order.order_id}")
        except Exception as e:
            order.status = OrderStatus.FAILED
            logging.error(f"Failed to place PolyMarket order: {e}")

    def cancel_order(self, order: Order) -> None:
        """
        Cancel a specific order on the PolyMarket platform.
        """
        if not order.order_id:
            logging.error("Cannot cancel PolyMarket order: order_id is not set.")
            order.status = OrderStatus.FAILED
            return

        try:
            # The py_clob_client.cancel method takes the order hash.
            response = self.client.cancel(order.order_id)
            logging.info(f"PolyMarket cancel order response: {response}")
            
            # The client library raises an exception on failure. If we get here,
            # it means the cancellation was accepted by the API.
            order.status = OrderStatus.CANCELED
            logging.info(f"Order {order.order_id} cancelled successfully on PolyMarket.")
        except Exception as e:
            logging.error(f"Failed to cancel PolyMarket order {order.order_id}: {e}")


    def get_order_status(self, order: Order) -> List[Trade]:
        """
        Get the status of a specific order from the PolyMarket platform, 
        update the order object, and return any new fills.
        """
        if not order.order_id:
            logging.error("Cannot get PolyMarket order status: order_id is not set.")
            order.status = OrderStatus.FAILED
            return []

        try:
            order_data = self.client.get_order(order.order_id)
            
            polymarket_status = order_data.get("status")
            original_size = float(order_data.get("original_size", 0))
            size_matched = float(order_data.get("size_matched", 0))

            if polymarket_status == "cancelled":
                order.status = OrderStatus.CANCELED
            elif size_matched >= original_size and original_size > 0:
                order.status = OrderStatus.EXECUTED
            elif size_matched > 0:
                order.status = OrderStatus.PARTIALLY_FILLED
            elif polymarket_status == "open":
                order.status = OrderStatus.OPEN
            
            order.fill_size = int(size_matched)
            
            # Fetch and return fills
            if order_data.get("associate_trades"):
                new_trades = []
                for trade_id in order_data["associate_trades"]:
                    trade_data = self._get_trade(trade_id)
                    new_trades.append(Trade(
                        order_id=order.id,
                        platform_trade_id=trade_data['id'],
                        quantity=int(float(trade_data['size'])),
                        price=int(float(trade_data['price']) * 100),
                        executed_at=trade_data['timestamp'] 
                    ))
                logging.info(f"Found {len(new_trades)} new fills for order {order.order_id}.")
                return new_trades

            logging.info(f"Updated PolyMarket order {order.order_id} status to {order.status.value}, Fill Size: {order.fill_size}")

        except Exception as e:
            logging.error(f"Failed to get PolyMarket order status for {order.order_id}: {e}")

        return []

    def _get_token_id(self, market_id: str, side: str) -> str:
        cid_to_tkd = asyncio.run(self._fetch_all_cid_to_tkd(self.base_url, [market_id]))
        if side.lower() == 'yes':
            return cid_to_tkd[market_id][0]
        elif side.lower() == 'no':
            return cid_to_tkd[market_id][1]
        else:
            raise ValueError(f"Invalid side: {side}")