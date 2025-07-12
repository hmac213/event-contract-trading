from backend.models.PlatformType import PlatformType
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform

class Manager():

    def __init__(self):
        self.platforms = {PlatformType.KALSHI: KalshiPlatform(),
                         PlatformType.POLYMARKET: PolyMarketPlatform()}
    
    def update(self):
        """
        Update all tasks, including
        Pulling Market ID from each platform
        Check with the database if the market ID exists
        """
        pass