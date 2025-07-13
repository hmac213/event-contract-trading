from backend.core.Similarity import Similarity
from backend.models.PlatformType import PlatformType
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.db.DBManager import DBManager
import logging
from datetime import datetime
from backend.core.CrossPlatformArbitrage import calculate_cross_platform_arbitrage
import threading
import time
from datetime import datetime


class Manager():

    def __init__(self, verbose: bool = False):
        self.platforms = {PlatformType.KALSHI: KalshiPlatform(),
                         PlatformType.POLYMARKET: PolyMarketPlatform()}
        self.db_manager = DBManager()
        self.logger = logging.getLogger(__name__)
    
        self.set_verbose(verbose)

    def set_verbose(self, verbose: bool):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='[%(asctime)s] %(levelname)s: %(message)s')
    def continuous_trading_engine(self):
        # Start market updater in a separate thread
        threading.Thread(target=self._market_updater, daemon=True).start()
        
        # Arbitrage check loop runs continuously
        while True:
            start_time = datetime.now()
            self.logger.info("Checking arbitrage opportunities...")
            self.check_arbitrage()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("Arbitrage Check Duration: %d ms", duration_ms)

    def _market_updater(self):
        while True:
            start_time = datetime.now()
            self.logger.info("Starting Market Update")
            self.update_markets()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("Market Update Duration: %d ms", duration_ms)
            time.sleep(60)  # Wait 60 seconds before next update

    def update_markets(self):
        # Update markets from all platforms
        self.logger.info("Checking for new markets...")
        cross_platform_new_markets = []
        for platform in self.platforms.values():
            start_time = datetime.now()
            self.logger.info(f"Fetching new markets for platform {platform.__class__.__name__}")
            platform_new_market_ids = platform.find_new_markets(20)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info(f"Fetched {len(platform_new_market_ids)} new markets in {duration_ms} ms")

            db_new_market_ids = self.db_manager.new_markets(platform_new_market_ids)
            if db_new_market_ids:
                # Get full market objects before adding to database
                new_market_objects = platform.get_markets(db_new_market_ids)
                self.db_manager.add_markets(new_market_objects)
                cross_platform_new_markets.extend(new_market_objects)
        
        
        if cross_platform_new_markets:
            start_time = datetime.now()
            self.logger.info("Checking for market similarities...")
            all_pairings = Similarity.check_similarity(cross_platform_new_markets)
            self.db_manager.add_market_pairs(all_pairings)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("Market Similarity Check Duration: %d ms", duration_ms)
        

    def check_arbitrage(self):
        self.logger.info("Checking for arbitrage opportunities...")
        market_pairs = self.db_manager.get_all_market_pairs()

        # Step 1: Collect all unique market IDs across all pairs
        unique_market_ids = set()
        for pair in market_pairs:
            unique_market_ids.update(pair)

        # Step 2: Get all Market objects in one DB call
        markets = self.db_manager.get_markets(list(unique_market_ids))

        # Step 3: Group market IDs by platform for batch orderbook fetching
        market_ids_by_platform = {}
        for market in markets:
            market_ids_by_platform.setdefault(market.platform, []).append(market.market_id)

        # Step 4: Fetch all orderbooks in bulk per platform
        all_orderbooks = []
        for platform, ids in market_ids_by_platform.items(): 
            start_time = datetime.now()
            logging.info(f"Fetching order books for platform {platform}")
            orderbooks = self.platforms[platform].get_order_books(ids)
            all_orderbooks.extend(orderbooks)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logging.info(f"Fetched {len(orderbooks)} order books for platform {platform} in {duration_ms} ms")

        ids_to_orderbook = {order_book.market_id: order_book for order_book in all_orderbooks}
        # Step 5: Store all orderbooks
        self.db_manager.add_orderbooks(all_orderbooks)
        # Step 6: Calculate arbitrage opportunities
        start_time = datetime.now()

        for pair in market_pairs:
            results = calculate_cross_platform_arbitrage(ids_to_orderbook[pair[0]], ids_to_orderbook[pair[1]], 0.01, 0.0025)
            logging.info(
                "Cross Platform Arbitrage Opportunities: \n %s and %s:\n"
                "  Market 1 - YES: %s, NO: %s\n"
                "  Market 2 - YES: %s, NO: %s",
                pair[0], pair[1],
                results[0], results[1], results[3], results[2]
            )
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)


if __name__ == "__main__":
    manager = Manager(verbose=False)
    manager.continuous_trading_engine()