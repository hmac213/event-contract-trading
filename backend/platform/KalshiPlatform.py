from datetime import datetime
import time
from typing import List
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.platform.BasePlatform import BasePlatform, PlatformType
import requests
from dotenv import load_dotenv

load_dotenv()  
class KalshiPlatform(BasePlatform):
    """
    Kalshi Platform implementation that interfaces with the Kalshi API.

    Kalshi is a prediction market platform that allows users to trade on
    the outcome of real-world events.
    """
    
    def __init__(self):
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

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
            response = self.session.get(f"{self.base_url}/markets/{market_id}/orderbook")
            if response.status_code == 200:
                data = response.json()["orderbook"]

                yes_bids = [[], []]
                yes_asks = [[], []]
                no_bids = [[], []]
                no_asks = [[], []]
                # if yes max price > no max price, 
                # then 


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
        for market_id in market_ids:
            response = self.session.get(f"{self.base_url}/markets/{market_id}")
            if response.status_code == 200:
                data = response.json()["market"]
                close_iso_time = data["close_time"]
                dt = datetime.strptime(close_iso_time, "%Y-%m-%dT%H:%M:%SZ")
                unix_ts = int(dt.timestamp())

                market = Market(
                    platform=PlatformType.KALSHI,
                    market_id=data['ticker'],
                    name=data['title'],
                    rules=data['rules_primary'],
                    close_timestamp=unix_ts
                )
                markets.append(market)
            else:
                print(f"Failed to fetch market {market_id}: {response.status_code} - {response.text}")

        return markets

