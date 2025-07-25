import time
import os
import signal
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform
from platforms.TestPlatform import TestPlatform
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
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def poll_markets(self):
        """
        Polls for markets from all platforms and adds them to a Redis Stream.
        """
        print("Polling for new markets...")
        for platform in self.platforms:
            try:
                market_ids = platform.find_new_markets(100)
                markets = platform.get_markets(market_ids)
                for market in markets:
                    market_data = {
                        "market_id": market.market_id,
                        "platform": market.platform.value,
                        "name": market.name,
                        "rules": market.rules
                    }
                    self.redis_manager.add_to_stream(self.stream_name, market_data)
                platform_name = "Unknown"
                if hasattr(platform, 'PLATFORM'):
                    platform_name = platform.PLATFORM.value
                elif isinstance(platform, KalshiPlatform):
                    platform_name = "Kalshi"
                elif isinstance(platform, PolyMarketPlatform):
                    platform_name = "PolyMarket"
                elif isinstance(platform, TestPlatform):
                    platform_name = "Test"
                print(f"Found and streamed {len(markets)} markets on {platform_name}")
            except Exception as e:
                platform_name = "Unknown"
                if hasattr(platform, 'PLATFORM'):
                    platform_name = platform.PLATFORM.value
                elif isinstance(platform, KalshiPlatform):
                    platform_name = "Kalshi"
                elif isinstance(platform, PolyMarketPlatform):
                    platform_name = "PolyMarket"
                elif isinstance(platform, TestPlatform):
                    platform_name = "Test"
                print(f"Error polling from {platform_name}: {e}")

    def run(self):
        """
        Runs the polling service indefinitely.
        """
        polling_interval = int(os.getenv("POLLING_INTERVAL_S", 60))
        print(f"Starting Market Polling Service with a {polling_interval} second interval...")
        while not self.shutdown_requested:
            self.poll_markets()
            # The sleep is interruptible by signals, so we check the flag again.
            if not self.shutdown_requested:
                time.sleep(polling_interval)
        print("Market Polling Service shut down gracefully.")

if __name__ == '__main__':
    polling_service = MarketPollingService()
    polling_service.run()
