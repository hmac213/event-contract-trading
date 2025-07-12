# extends Base Market
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.platform.BasePlatform import BasePlatform
from backend.models.PlatformType import PlatformType
from random import randint, random
import time
import string
import random

class TestPlatform(BasePlatform):
    def get_order_books(self, market_ids: list[str]) -> list[Orderbook]:

        if market_ids is None:
            return []
        
        ans = []
        for market_id in market_ids:
            # for each market_id, create a dummy order book
            
            # price, quantity pairs for yes and no
            yes_bids = [sorted(randint(1, 500) for _ in range(100)), [randint(1, 20000) for _ in range(100)]]
            # no ask is the same as yes bids, but each of the price is 1000 - price
            no_asks = [[1000 - price for price in yes_bids[0]], [a_quantity for a_quantity in yes_bids[1]]]


            no_bids = [sorted(randint(500, 1000) for _ in range(100)), [randint(1, 20000) for _ in range(100)]]
            yes_asks = [[1000 - price for price in no_bids[0]], [a_quantity for a_quantity in no_bids[1]]]
            orderbook = Orderbook(
                market_id=market_id,
                timestamp= int(time.time() * 1000),
                yes={"bid": yes_bids,
                     "ask": yes_asks},
                no={"bid": no_bids,
                    "ask": no_asks}
            )
            ans.append(orderbook)
        return ans

    def find_new_markets(self, num_markets: int) -> list[str]:


        # generate a list of random market IDs that are 64 characters long
        if num_markets <= 0:
            return []
        chars = string.ascii_lowercase + string.digits
        return [''.join(random.choices(chars, k=64)) for _ in range(num_markets)]
    

    def get_markets(self, market_ids: list[str]) -> list[Market]:

        # create a dummy market
        return [Market(
            platform=PlatformType.TEST,
            market_id=market_id,
            name='Name of Market for ' + market_id,
            rules='Test Rules regarding ' + market_id,
            close_timestamp=int(time.time() * 1000)
        ) for market_id in market_ids]