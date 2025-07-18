import unittest
from models.Orderbook import Orderbook
from services.arbitrage_finder.calculator import calculate_cross_platform_arbitrage

class TestArbitrageCalculator(unittest.TestCase):

    def test_arbitrage_opportunity_found(self):
        """
        Test that an arbitrage opportunity is found when one exists.
        """
        # Arrange
        orderbook1 = Orderbook(
            market_id="1",
            timestamp=123456789,
            yes={"bid": [], "ask": [[10, 100]]},
            no={"bid": [], "ask": [[80, 100]]}
        )
        orderbook2 = Orderbook(
            market_id="2",
            timestamp=123456789,
            yes={"bid": [], "ask": [[20, 100]]},
            no={"bid": [], "ask": [[70, 100]]}
        )
        
        # Act
        opportunity = calculate_cross_platform_arbitrage(orderbook1, orderbook2)
        
        # Assert
        self.assertIsNotNone(opportunity)
        self.assertEqual(opportunity["type"], "yes1_no2")
        self.assertGreater(opportunity["shares"], 0)

    def test_no_arbitrage_opportunity(self):
        """
        Test that no arbitrage opportunity is found when one does not exist.
        """
        # Arrange
        orderbook1 = Orderbook(
            market_id="1",
            timestamp=123456789,
            yes={"bid": [], "ask": [[500, 100]]},
            no={"bid": [], "ask": [[500, 100]]}
        )
        orderbook2 = Orderbook(
            market_id="2",
            timestamp=123456789,
            yes={"bid": [], "ask": [[500, 100]]},
            no={"bid": [], "ask": [[500, 100]]}
        )
        
        # Act
        opportunity = calculate_cross_platform_arbitrage(orderbook1, orderbook2)
        
        # Assert
        self.assertIsNone(opportunity)

if __name__ == '__main__':
    unittest.main() 