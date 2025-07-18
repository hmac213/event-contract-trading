import unittest
from unittest.mock import MagicMock, patch
from services.arbitrage_finder.main import ArbitrageFinderService, PlatformType
from models.Orderbook import Orderbook

class TestArbitrageFinderService(unittest.TestCase):

    @patch('services.arbitrage_finder.main.RedisManager')
    @patch('services.arbitrage_finder.main.KalshiPlatform')
    @patch('services.arbitrage_finder.main.PolyMarketPlatform')
    def test_process_market_pairs_with_arbitrage_opportunity(self, MockPolyMarketPlatform, MockKalshiPlatform, MockRedisManager):
        # Arrange
        mock_redis_manager = MockRedisManager.return_value
        mock_kalshi_platform = MockKalshiPlatform.return_value
        mock_polymarket_platform = MockPolyMarketPlatform.return_value

        # Mock Redis to return one message
        message_id = '12345-0'
        message_data = {
            'market_id_1': 'KALSHI_MARKET_1', 'platform_1': PlatformType.KALSHI.value,
            'market_id_2': 'POLY_MARKET_1', 'platform_2': PlatformType.POLYMARKET.value
        }
        mock_redis_manager.read_from_stream.return_value = [(message_id, message_data)]

        # Mock platforms to return orderbooks with a clear arbitrage opportunity
        orderbook1 = Orderbook(market_id="KALSHI_MARKET_1", timestamp=123, yes={"ask": [[400, 10]], "bid": []}, no={"ask": [[600, 10]], "bid": []})
        orderbook2 = Orderbook(market_id="POLY_MARKET_1", timestamp=123, yes={"ask": [[600, 10]], "bid": []}, no={"ask": [[400, 10]], "bid": []})
        mock_kalshi_platform.get_order_books.return_value = [orderbook1]
        mock_polymarket_platform.get_order_books.return_value = [orderbook2]

        # Act
        service = ArbitrageFinderService()
        service.process_market_pairs()

        # Assert
        # Check that an opportunity was published to Redis
        mock_redis_manager.add_to_stream.assert_called_once()
        # Check that the original message was acknowledged
        mock_redis_manager.acknowledge_message.assert_called_with(service.input_stream_name, service.group_name, message_id)

    @patch('services.arbitrage_finder.main.RedisManager')
    @patch('services.arbitrage_finder.main.KalshiPlatform')
    @patch('services.arbitrage_finder.main.PolyMarketPlatform')
    def test_process_market_pairs_no_arbitrage_opportunity(self, MockPolyMarketPlatform, MockKalshiPlatform, MockRedisManager):
        # Arrange
        mock_redis_manager = MockRedisManager.return_value
        mock_kalshi_platform = MockKalshiPlatform.return_value
        mock_polymarket_platform = MockPolyMarketPlatform.return_value

        message_id = '12345-0'
        message_data = {
            'market_id_1': 'KALSHI_MARKET_1', 'platform_1': PlatformType.KALSHI.value,
            'market_id_2': 'POLY_MARKET_1', 'platform_2': PlatformType.POLYMARKET.value
        }
        mock_redis_manager.read_from_stream.return_value = [(message_id, message_data)]

        # Mock platforms to return orderbooks with no arbitrage opportunity
        orderbook1 = Orderbook(market_id="KALSHI_MARKET_1", timestamp=123, yes={"ask": [[500, 10]], "bid": []}, no={"ask": [[500, 10]], "bid": []})
        orderbook2 = Orderbook(market_id="POLY_MARKET_1", timestamp=123, yes={"ask": [[510, 10]], "bid": []}, no={"ask": [[510, 10]], "bid": []})
        mock_kalshi_platform.get_order_books.return_value = [orderbook1]
        mock_polymarket_platform.get_order_books.return_value = [orderbook2]
        
        # Act
        service = ArbitrageFinderService()
        service.process_market_pairs()

        # Assert
        # Check that NO opportunity was published
        mock_redis_manager.add_to_stream.assert_not_called()
        # Check that the message was still acknowledged
        mock_redis_manager.acknowledge_message.assert_called_with(service.input_stream_name, service.group_name, message_id)

if __name__ == '__main__':
    unittest.main() 