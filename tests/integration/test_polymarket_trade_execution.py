import unittest
import time
from platforms.PolyMarketPlatform import PolyMarketPlatform
from models.Order import Order
from models.OrderStatus import OrderStatus
from dotenv import load_dotenv

load_dotenv()

class TestPolyMarketTradeExecution(unittest.TestCase):

    def setUp(self):
        """Set up the PolyMarket platform client before each test."""
        self.platform = PolyMarketPlatform()

    def test_polymarket_trade_lifecycle(self):
        """
        Tests the full lifecycle of a trade on the PolyMarket platform:
        1. Find an active market.
        2. Place a small limit order.
        3. Verify the order is open.
        4. Cancel the order.
        5. Verify the order is canceled.
        """
        # 1. Find an active market
        active_markets = self.platform.find_new_markets(1)
        self.assertGreater(len(active_markets), 0, "No active markets found on PolyMarket.")
        market_id = active_markets[0]

        # 2. Place a small limit order
        # We place a limit buy for 1 cent, which is unlikely to be filled.
        # The minimum order size on PolyMarket is 5.
        order = Order.create_limit_buy_order(
            market_id=market_id,
            side="yes",
            size=5,
            price=1 
        )
        self.platform.place_order(order)
        self.assertIsNotNone(order.order_id, "Order ID was not set after placing order.")
        
        # 3. Verify the order is open
        # Allow some time for the order to be processed
        time.sleep(15)
        self.platform.get_order_status(order)
        self.assertEqual(order.status, OrderStatus.OPEN, f"Order status is not OPEN. Current status: {order.status}")

        # 4. Cancel the order
        self.platform.cancel_order(order)
        
        # 5. Verify the order is canceled
        time.sleep(2)
        self.platform.get_order_status(order)
        self.assertEqual(order.status, OrderStatus.CANCELED, f"Order status is not CANCELED. Current status: {order.status}")

if __name__ == '__main__':
    unittest.main() 