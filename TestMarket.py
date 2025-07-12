# extends Base Market

from BaseMarket import BaseMarket
from typing import Dict, Any


class TestMarket(BaseMarket):
    def get_order_books(self, market_ids: list[str]) -> list[Dict[str, Any]]:
        # Implement your test logic here

        if market_ids is None:
            return []
        
        ans = []


        for market_id in market_ids:
            # for each market_id, create a dummy order book
            order_book = {
                'bids': [{'price': 100, 'quantity': 10}],
                'asks': [{'price': 110, 'quantity': 5}],
            }
            ans.append(order_book)

    def get_markets(self, num_markets: int) -> list[str]:
        # Implement your test logic here
        # generate a list of random market IDs that are 64 characters long
        if num_markets <= 0:
            return []
        return [f"market_{i:064d}" for i in range(num_markets)]
    