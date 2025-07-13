from datetime import datetime
import time
from typing import List
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.platform.BasePlatform import BasePlatform
from py_clob_client.client import ClobClient 
from py_clob_client.clob_types import BookParams
from dotenv import load_dotenv
import os
import requests
from backend.models.PlatformType import PlatformType
import logging
import json

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
        self.client = ClobClient(host, key=key, chain_id=chain_id, signature_type=2, funder=POLYMARKET_PROXY_ADDRESS)

        # for Gamma API access
        self.base_url = "https://gamma-api.polymarket.com"

    def get_order_books(self, market_ids: List[str]) -> List[Orderbook]:
        
        """
        Get order books for the specified market IDs.
        
        Args:
            market_ids: List of market IDs to get order books for
            
        Returns:
            List of Orderbook objects containing bid/ask data
        """

        market_id_set = set(market_ids)

        offset = 0
        limit = 1000
        seen_ids = set()

        # str -> [str, str]
        cid_to_tkd = {}

        tkd_to_order_book = {}
        

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
                    cid_to_tkd[cid] = json.loads(m["clobTokenIds"])
                    seen_ids.add(cid)
            offset += 1000
 
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
        new_markets = set()
        page_offset = 0
        while num_requests < num_markets:
            # https://gamma-api.polymarket.com/markets?order=id&closed=false&active=true&ascending=false
            response = requests.request("GET", f"{self.base_url}/markets?order=id&closed=false&active=true&ascending=false&limit=1000&offset={page_offset}")

            for a_market in response.json():
                if a_market.get("endDateIso") is not None and a_market["endDateIso"] is not None:
                    condition_id = a_market.get("conditionId")
                    if condition_id and condition_id not in new_markets:
                        new_markets.add(condition_id)
                        num_requests += 1
                        if num_requests >= num_markets:
                            break
            page_offset += 1000
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
        matched_markets = []

        offset = 0
        limit = 1000
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
            offset += 1000

        return matched_markets

