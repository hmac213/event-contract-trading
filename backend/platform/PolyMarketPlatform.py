from datetime import datetime
import time
from typing import List, Dict
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.platform.BasePlatform import BasePlatform
from backend.models.PlatformType import PlatformType
from py_clob_client.client import ClobClient 
from py_clob_client.clob_types import BookParams
from dotenv import load_dotenv
import os

load_dotenv()  
class PolyMarketPlatform(BasePlatform):
    """
    PolyMarket Platform implementation that interfaces with the PolyMarket GraphQL API.
    
    PolyMarket is a prediction market platform that allows users to trade on
    the outcome of real-world events.
    """
    
    def __init__(self):
        host: str = "https://clob.polymarket.com"
        key: str = os.getenv("PRIVATE_KEY")
        POLYMARKET_PROXY_ADDRESS : str = os.getenv("PROXY_ADDRESS")
        chain_id: int = 137
        self.client = ClobClient(host, key=key, chain_id=chain_id, signature_type=2, funder=POLYMARKET_PROXY_ADDRESS)

    def get_order_books(self, market_ids: List[str]) -> List[Orderbook]:
        
        """
        Get order books for the specified market IDs.
        
        Args:
            market_ids: List of market IDs to get order books for
            
        Returns:
            List of Orderbook objects containing bid/ask data
        """

        orderbooks = []
        for market_id in market_ids:
            polymarket_market = self.client.get_market(condition_id=market_id)

            yes_token = polymarket_market["tokens"][0]["token_id"]
            yes_order_book = self.client.get_order_book(token_id=yes_token)
            no_token = polymarket_market["tokens"][1]["token_id"]
            no_order_book = self.client.get_order_book(token_id=no_token)

            yes_book = {
                    "bid": [[], []],
                    "ask": [[], []]
                }

            # get yes bid
            for an_order_summary in yes_order_book.bids:
                yes_book["bid"][0].append(int(float(an_order_summary.price) * 1000))  # Convert to integer cents
                yes_book["bid"][1].append(int(float(an_order_summary.size) * 100))

            # get yes ask
            for an_order_summary in yes_order_book.asks:
                yes_book["ask"][0].append(int(float(an_order_summary.price) * 1000))  # Convert to integer cents
                yes_book["ask"][1].append(int(float(an_order_summary.size) * 100))

            no_book = {
                "bid": [[], []],
                "ask": [[], []]
            }
            
            # get no bid
            for an_order_summary in no_order_book.bids:
                no_book["bid"][0].append(int(float(an_order_summary.price) * 1000))  # Convert to integer cents
                no_book["bid"][1].append(int(float(an_order_summary.size) * 100))

            # get no ask
            for an_order_summary in no_order_book.asks:
                no_book["ask"][0].append(int(float(an_order_summary.price) * 1000))  # Convert to integer cents
                no_book["ask"][1].append(int(float(an_order_summary.size) * 100))

            orderbook = Orderbook(
                market_id=market_id,
                timestamp=int(time.time() * 1000),
                yes=yes_book,
                no=no_book  
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
        new_markets = []
        next_cursor = ""

        while num_requests < num_markets and next_cursor != "LTE=":
            req = self.client.get_simplified_markets(next_cursor=next_cursor)
            next_cursor = req.get("next_cursor", "LTE=")

            for a_market in req["data"]:

                # check if we want to include this market
                condition_id_exists = a_market["condition_id"] is not None and a_market["condition_id"] != ""

                # uses yes and no tokens to determine if the market is active
                uses_binary_tokens = a_market["tokens"][0]["outcome"] == "Yes" and a_market["tokens"][1]["outcome"] == "No" 

                market_is_active = a_market["active"] and a_market["closed"] is False
                if condition_id_exists and uses_binary_tokens and market_is_active:
                    new_markets.append(a_market["condition_id"])
                    num_requests += 1
                    if num_requests >= num_markets:
                        break
        return new_markets
    
    def get_markets(self, market_ids: List[str]) -> List[Market]:
        """
        Get market details for the specified market IDs.
        
        Args:
            market_ids: List of market IDs to get details for
            
        Returns:
            List of Market objects with market information
        """
        ans = []
        for market_id in market_ids:
            a_polymarket_market = self.client.get_market(condition_id=market_id)
            a_token = a_polymarket_market["tokens"]
            close_iso_time = a_polymarket_market["end_date_iso"]
            dt = datetime.strptime(close_iso_time, "%Y-%m-%dT%H:%M:%SZ")

            unix_ts = int(dt.timestamp())
            ans.append(Market(
                platform=PlatformType.POLYMARKET,
                market_id=market_id,
                name=a_polymarket_market["question"],  
                rules= "Binary Token 0: " + a_token[0]["outcome"] + ", Binary Token 1: " + a_token[1]["outcome"],  
                close_timestamp=unix_ts
            ))

        return ans

