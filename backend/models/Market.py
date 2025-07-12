from backend.platform.BasePlatform import PlatformType

class Market():
    def __init__(self, platform: PlatformType,market_id: str, name: str, rules: str, close_timestamp: int):
        self.platform= platform
        self.market_id = market_id
        self.name = name
        self.rules = rules
        self.close_timestamp = close_timestamp

    