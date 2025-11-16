from models.PlatformType import PlatformType
import time
from typing import Optional

class Market():
    def __init__(self, platform: PlatformType, market_id: str, name: str, rules: str, close_timestamp: Optional[int] = None):
        self.platform = platform
        self.market_id = market_id
        self.name = name
        self.rules = rules
        # Default to far future if not provided (robust fallback)
        self.close_timestamp = close_timestamp if close_timestamp is not None else int(time.time() * 1000) + (365 * 24 * 60 * 60 * 1000)  # 1 year from now
    
    @classmethod
    def from_stream_data(cls, data: dict):
        """
        Create Market from Redis stream data with robust field handling.
        """
        return cls(
            platform=PlatformType(data['platform']),
            market_id=data['market_id'],
            name=data['name'],
            rules=data['rules'],
            close_timestamp=data.get('close_timestamp')  # Use .get() for optional field
        )

    