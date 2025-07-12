from datetime import datetime
import time
from typing import List
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.platform.BasePlatform import BasePlatform
from backend.models.PlatformType import PlatformType
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
            response2 = self.session.get(f"{self.base_url}/markets/{market_id}")
            if response.status_code == 200 and response2.status_code == 200:

                data = response.json()["orderbook"]
                data2 = response2.json()["market"]
                highest_no_bid = data2["no_bid"]
                highest_yes_bid = data2["yes_bid"]


                yes_bids = [[], []]
                yes_asks = [[], []]
                no_bids = [[], []]
                no_asks = [[], []]
                
                yes = data["yes"]
                no = data["no"] 
                for a_yes in yes:
                    if a_yes[0] < highest_yes_bid:
                        yes_bids[0].append(a_yes[0] * 10)
                        yes_bids[1].append(a_yes[1] * 100)
                for a_no in no:
                    if a_no[0] < highest_no_bid:
                        no_bids[0].append(a_no[0] * 10)
                        no_bids[1].append(a_no[1] * 100)

                for i in range(len(yes_bids[0])):
                    no_asks[0].append(1000 - yes_bids[0][i])
                    no_asks[1].append(yes_bids[1][i])
                for i in range(len(no_bids[0])):
                    yes_asks[0].append(1000 - no_bids[0][i])
                    yes_asks[1].append(no_bids[1][i])

                
               
                orderbook = Orderbook(
                    market_id=market_id,
                    timestamp=int(time.time() * 1000),
                    yes={"bid": yes_bids, "ask": yes_asks},
                    no={"bid": no_bids, "ask": no_asks}
                )

                orderbooks.append(orderbook)

        return orderbooks

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

