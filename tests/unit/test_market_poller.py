from services.market_poller.main import MarketPollingService
import unittest

class SpyRedisManager:
    def __init__(self):
        self.calls = []

    def add_to_stream(self, stream_name, data):
        self.calls.append({"stream_name": stream_name, "data": data})

class TestMarketPoller(unittest.TestCase):
    def test_poll_markets_with_real_platforms(self):
        # Arrange
        service = MarketPollingService()
        spy_redis_manager = SpyRedisManager()

        # Monkey-patch the redis_manager to use our spy
        service.redis_manager = spy_redis_manager

        # Act
        # This will make real API calls to the platforms
        service.poll_markets()

        # Assert
        # We assert that at least one market was processed, as live data can vary.
        self.assertGreater(len(spy_redis_manager.calls), 0, "No markets were streamed to Redis.")

    # Check the structure of the first streamed item
        first_call = spy_redis_manager.calls[0]
        self.assertEqual(first_call['stream_name'], "market_events_stream")
    
        market_data = first_call['data']
        self.assertIn("market_id", market_data)
        self.assertIn("platform", market_data)
        self.assertIn("name", market_data)
        self.assertIn("rules", market_data)
    
        print(f"\nSuccessfully streamed {len(spy_redis_manager.calls)} markets.")

if __name__ == "__main__":
    unittest.main()