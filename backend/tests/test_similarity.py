from backend.core.Similarity import Similarity
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.core.CrossPlatformArbitrage import calculate_cross_platform_arbitrage
from backend.db.DBManager import DBManager


kalshi = KalshiPlatform()
polymarket = PolyMarketPlatform()
db_manager = DBManager()


# RobotTaxi
kalshi_market_str = "ROBOTAXIOUT-26-JAN01"
polymarket_market_str = "0x642415ca4ea8d6ccdd8133af34cbe4991bc84ad27bb3ab0fa2cf38c6aa20b39d"

# Open AI 
kalshi_market_2_str = "OAIAGI-25"
polymarket_market_2_str = "0x310c3d08f015157ec78e04f3f4fefed659b5e2bd88ae80cb38ff27ef970c39bd"

# Next CEO of X (This one had no arbitrage when I checked)
kalshi_market_3_str = "KXNEWROLEX-26JAN-EMUS"
polymarket_market_3_str = "0x4a51e4c89437c1c792c8fd2bb834e937b5795e2a27de1c1ad0018c99469efc33"

all_markets = []

kalshi_markets = kalshi.get_markets([kalshi_market_str, kalshi_market_2_str, kalshi_market_3_str]) 
polymarket_markets = polymarket.get_markets([polymarket_market_str, polymarket_market_2_str, polymarket_market_3_str])

all_markets.extend(kalshi_markets)
all_markets.extend(polymarket_markets)

print(f"  Total Markets: {len(all_markets)}")
result = Similarity.check_similarity(new_markets=all_markets)

print("Similarity Check:")
for row_idx, row in enumerate(result):
    print(f"  Row {row_idx}:")
    for col_idx, item in enumerate(row):
        print(f"    [{row_idx}][{col_idx}] {type(item).__name__}")
        if hasattr(item, '__dict__'):
            for k, v in item.__dict__.items():
                print(f"      {k}: {v}")
        else:
            print(f"      {item}")
