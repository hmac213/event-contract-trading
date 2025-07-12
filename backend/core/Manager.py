from backend.core.Similarity import Similarity
from backend.models.PlatformType import PlatformType
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.db.DBManager import DBManager
import logging
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
        while True:
            self.trading_engine()

    def trading_engine(self):
        start_time = datetime.now()
        self.logger.info("Starting Trading Engine Cycle")
        self.update_markets()
        self.check_arbitrage()
        self.logger.info("Ending Trading Engine Cycle")
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        self.logger.info("Cycle Duration: %d ms", duration_ms)

    def update_markets(self):
        # Update markets from all platforms
        self.logger.info("Checking for new markets...")
        cross_platform_new_markets = []
        for platform in self.platforms.values():
            platform_new_market_ids = platform.find_new_markets(20)
            db_new_market_ids = self.db_manager.new_markets(platform_new_market_ids)
            if db_new_market_ids:
                # Get full market objects before adding to database
                new_market_objects = platform.get_markets(db_new_market_ids)
                self.db_manager.add_markets(new_market_objects)
                cross_platform_new_markets.extend(new_market_objects)
        
        if cross_platform_new_markets:
            all_pairings = Similarity.check_similarity(cross_platform_new_markets)
            self.db_manager.add_market_pairs(all_pairings)
            

    def check_arbitrage(self):
        self.logger.info("Checking for arbitrage opportunities...")
        market_pairs = self.db_manager.get_all_market_pairs()
        self.logger.info("Got market pairs: %s", market_pairs)

        for pair in market_pairs:
            orderbooks = self.db_manager.get_orderbooks(pair)
        

if __name__ == "__main__":
    manager = Manager(verbose=False)
    manager.continuous_trading_engine()