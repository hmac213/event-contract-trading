"""
Platform package for event contract trading.

This package contains platform-specific implementations for different trading platforms.
"""

# Import order is important to avoid circular imports
# BasePlatform should be imported first since other classes depend on it

__all__ = ['BasePlatform', 'KalshiPlatform', 'PolyMarketPlatform', 'TestPlatform']
