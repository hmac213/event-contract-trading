from backend.core.CrossPlatformArbitrage import calculate_cross_platform_arbitrage
from backend.models.Orderbook import Orderbook
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform

kalshi = KalshiPlatform()
polymarket = PolyMarketPlatform()

print('fetching orderbooks')

kob = kalshi.get_order_books(['OAIAGI-25'])[0]
pob = polymarket.get_order_books(['0x310c3d08f015157ec78e04f3f4fefed659b5e2bd88ae80cb38ff27ef970c39bd'])[0]

print(f"kalshi yes: {kob.yes}\n")
print(f"kalshi no: {kob.no}\n")
print(f"pm yes: {pob.yes}\n")
print(f"pm no: {kob.no}\n")

MIN_PROFIT = 0.02
EXPECTED_SLIP = 0.1

print(calculate_cross_platform_arbitrage(kob, pob, MIN_PROFIT, EXPECTED_SLIP))

