import time
import os
from platform.KalshiPlatform import KalshiPlatform
from platform.PolyMarketPlatform import PolyMarketPlatform
from platform.TestPlatform import TestPlatform
from db.DBManager import DBManager
from cache.RedisManager import RedisManager

class MarketPollingService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.platforms = [
            KalshiPlatform(),
            PolyMarketPlatform(),
            TestPlatform()
        ]
        self.stream_name = "market_events_stream"

    def poll_markets(self):
        """
        Polls for markets from all platforms and adds them to a Redis Stream.
        """
        print("Polling for new markets...")
        for platform in self.platforms:
            try:
                markets = platform.get_all_markets()
                for market in markets:
                    market_data = {
                        "market_id": market.market_id,
                        "platform": market.platform.value,
                        "name": market.name,
                        "rules": market.rules
                    }
                    self.redis_manager.add_to_stream(self.stream_name, market_data)
                print(f"Found and streamed {len(markets)} markets on {platform.PLATFORM_NAME}")
            except Exception as e:
                print(f"Error polling from {platform.PLATFORM_NAME}: {e}")

    def run(self):
        """
        Runs the polling service indefinitely.
        """
        polling_interval = int(os.getenv("POLLING_INTERVAL_S", 60))
        print(f"Starting Market Polling Service with a {polling_interval} second interval...")
        while True:
            self.poll_markets()
            time.sleep(polling_interval)

if __name__ == '__main__':
    polling_service = MarketPollingService()
    polling_service.run()
