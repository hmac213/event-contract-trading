# extends Base Market
from models.Market import Market
from models.Orderbook import Orderbook
from platforms.BasePlatform import BasePlatform
from models.PlatformType import PlatformType
from random import randint, random
import time
import string
import random
from random import randint
from models.Order import Order

class TestPlatform(BasePlatform):
    def get_order_books(self, market_ids: list[str]) -> list[Orderbook]:

        if market_ids is None:
            return []
        
        ans = []
        for market_id in market_ids:
            # for each market_id, create a dummy order book
            

            # Generate yes bids as [price, quantity] pairs
            yes_bid_prices = sorted(randint(1, 500) for _ in range(100))
            yes_bid_quantities = [randint(1, 20000) for _ in range(100)]
            yes_bids = [[price, quantity] for price, quantity in zip(yes_bid_prices, yes_bid_quantities)]

            # Generate no asks as [1000 - price, quantity] pairs (mirrored from yes bids)
            no_asks = [[1000 - price, quantity] for price, quantity in zip(yes_bid_prices, yes_bid_quantities)]

            # Generate no bids as [price, quantity] pairs
            no_bid_prices = sorted(randint(500, 1000) for _ in range(100))
            no_bid_quantities = [randint(1, 20000) for _ in range(100)]
            no_bids = [[price, quantity] for price, quantity in zip(no_bid_prices, no_bid_quantities)]

            # Generate yes asks as [1000 - price, quantity] pairs (mirrored from no bids)
            yes_asks = [[1000 - price, quantity] for price, quantity in zip(no_bid_prices, no_bid_quantities)]

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

    def place_order(self, order: Order) -> dict:
        raise NotImplementedError

    def cancel_order(self, order: Order):
        raise NotImplementedError

    def get_order_status(self, order: Order) -> None:
        raise NotImplementedError