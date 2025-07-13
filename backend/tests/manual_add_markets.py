from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.core.CrossPlatformArbitrage import calculate_cross_platform_arbitrage
from backend.tests.test_depth_chart  import plot_depth_chart
from backend.db.DBManager import DBManager


kalshi = KalshiPlatform()
polymarket = PolyMarketPlatform()
db_manager = DBManager()


kalshi_market_str = "KXLLM1-25JUL31-GOOG"
polymarket_market_str = "0x310c3d08f015157ec78e04f3f4fefed659b5e2bd88ae80cb38ff27ef970c39bd"
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


