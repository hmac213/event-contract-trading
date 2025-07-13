from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.core.CrossPlatformArbitrage import calculate_cross_platform_arbitrage
from backend.db.DBManager import DBManager


kalshi = KalshiPlatform()
polymarket = PolyMarketPlatform()
db_manager = DBManager()


kalshi_market_str = "KXNEWROLEX-26JAN-EMUS"
polymarket_market_str = "0x4a51e4c89437c1c792c8fd2bb834e937b5795e2a27de1c1ad0018c99469efc33"
order_book_kalshi = kalshi.get_order_books([kalshi_market_str])[0]
order_book_polymarket = polymarket.get_order_books([polymarket_market_str])[0]

kalshi_market = kalshi.get_markets([kalshi_market_str])[0]
polymarket_market = polymarket.get_markets([polymarket_market_str])[0]
db_manager.add_markets([kalshi_market, polymarket_market])
db_manager.add_orderbooks([order_book_kalshi, order_book_polymarket])
db_manager.add_market_pairs([[kalshi_market, polymarket_market]])

print("Kalshi Order Book:", vars(order_book_kalshi))
print("Polymarket Order Book:", vars(order_book_polymarket))

print("Cross Platform Arbitrage Opportunities:" +
      str(calculate_cross_platform_arbitrage(order_book_kalshi, order_book_polymarket, 0.01, 0.0025)))


