from backend.core.Similarity import SimilarityManager
from backend.models.PlatformType import PlatformType
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.db.DBManager import DBManager
import logging
from datetime import datetime
from backend.core.CrossPlatformArbitrage import calculate_cross_platform_arbitrage
from backend.core.ExecuteArbitrage import ExecuteArbitrage
import threading
import time
from datetime import datetime


class Manager():

    def __init__(self, verbose: bool = False):
        self.platforms = {PlatformType.KALSHI: KalshiPlatform(),
                         PlatformType.POLYMARKET: PolyMarketPlatform()}
        self.db_manager = DBManager()
        self.logger = logging.getLogger(__name__)
        self.similarity_manager = SimilarityManager(self.db_manager)
    
        self.set_verbose(verbose)

    def set_verbose(self, verbose: bool):
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='[%(asctime)s] %(levelname)s: %(message)s')
    def continuous_trading_engine(self):
        # Initial market data population
        self.logger.info("Starting initial market data population...")
        self.update_markets()
        self.check_arbitrage()
        self.logger.info("Initial market data population complete.")
        
        # Start market updater in a separate thread
        threading.Thread(target=self._market_updater, daemon=True).start()
        
        # Arbitrage check loop runs continuously
        while True:
            start_time = datetime.now()
            self.logger.info("Checking arbitrage opportunities...")
            self.check_arbitrage()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("Arbitrage Check Duration: %d ms", duration_ms)
            time.sleep(5)

    def _market_updater(self):
        while True:
            time.sleep(1)
            start_time = datetime.now()
            self.logger.info("Starting Market Update")
            self.update_markets()
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("Market Update Duration: %d ms", duration_ms)

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
            self.logger.info("Adding new markets to similarity index...")
            self.similarity_manager.add_markets_to_index(cross_platform_new_markets)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("Finished adding markets to index in %d ms", duration_ms)

            start_time = datetime.now()
            self.logger.info("Checking for market similarities...")
            all_pairings = []
            for market in cross_platform_new_markets:
                similar_markets = self.similarity_manager.find_similar_markets(market.market_id)
                for similar_market in similar_markets:
                    pair = tuple(sorted((market.market_id, similar_market.market_id)))
                    all_pairings.append(pair)
            
            unique_pairings = list(set(all_pairings))

            if unique_pairings:
                self.db_manager.add_market_pairs(unique_pairings)

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

        # Filter out orderbooks that are empty
        all_orderbooks = [ob for ob in all_orderbooks if ob.yes and ob.no]
        if not all_orderbooks:
            self.logger.info("No non-empty orderbooks found.")
            return

        ids_to_market = {market.market_id: market for market in markets}
        ids_to_orderbook = {order_book.market_id: order_book for order_book in all_orderbooks}
        # Step 5: Store all orderbooks
        self.db_manager.add_orderbooks(all_orderbooks)
        # Step 6: Calculate arbitrage opportunities
        start_time = datetime.now()

        for pair in market_pairs:
            ob1 = ids_to_orderbook.get(pair[0])
            ob2 = ids_to_orderbook.get(pair[1])
            if not ob1 or not ob2:
                self.logger.warning(f"Order book missing for market pair: {pair[0]}, {pair[1]}")
                continue
            
            opportunity = calculate_cross_platform_arbitrage(ob1, ob2)
            if opportunity:
                self.logger.info(f"Arbitrage opportunity found for pair {pair[0]} and {pair[1]}: {opportunity}")
                market1 = ids_to_market[pair[0]]
                market2 = ids_to_market[pair[1]]
                
                platform1_obj = self.platforms[market1.platform]
                platform2_obj = self.platforms[market2.platform]
                
                # ExecuteArbitrage.place_arbitrage_orders(market1, market2, platform1_obj, platform2_obj, opportunity)

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        self.logger.info("Finished checking all pairs in %d ms", duration_ms)

if __name__ == "__main__":
    manager = Manager(verbose=False)
    manager.continuous_trading_engine()