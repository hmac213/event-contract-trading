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
        self.logger.debug("Starting Trading Engine Cycle")
        self.update_markets()
        self.check_arbitrage()
        self.logger.debug("Ending Trading Engine Cycle")
        pass
    
    def update_markets(self):
        # Update markets from all platforms
        for platform in self.platforms.values():
            platform_new_market_ids = platform.find_new_markets(10)
            db_new_market_ids = self.db_manager.new_markets(platform_new_market_ids)
            if db_new_market_ids:
                # Get full market objects before adding to database
                self.logger.debug(f"Adding new markets: {db_new_market_ids}")
                new_market_objects = platform.get_markets(db_new_market_ids)
                self.db_manager.add_markets(new_market_objects)
                # check similarity here & add similar markets to db
    def check_arbitrage(self):
        self.logger.debug("Checking for arbitrage opportunities...")
        pass
        

if __name__ == "__main__":
    manager = Manager(verbose=True)
    manager.continuous_trading_engine()