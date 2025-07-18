import time
import socket
import os
from cache.RedisManager import RedisManager
from db.DBManager import DBManager
from models.PlatformType import PlatformType
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform
from services.arbitrage_finder.calculator import calculate_cross_platform_arbitrage

class ArbitrageFinderService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.platforms = {
            PlatformType.KALSHI: KalshiPlatform(),
            PlatformType.POLYMARKET: PolyMarketPlatform()
        }
        
        self.input_stream_name = "similar_market_pairs_stream"
        self.output_stream_name = "arbitrage_opportunities_stream"
        self.group_name = "arbitrage_group"
        self.consumer_name = f"arbitrage-consumer-{socket.gethostname()}"
        
        self.redis_manager.create_consumer_group(self.input_stream_name, self.group_name)

    def process_market_pairs(self):
        """
        Processes market pairs from the Redis Stream, checks for arbitrage, and publishes opportunities.
        """
        print(f"Checking for new market pairs as consumer '{self.consumer_name}'...")
        messages = self.redis_manager.read_from_stream(self.input_stream_name, self.group_name, self.consumer_name)
        
        if not messages:
            print("No new market pairs.")
            return

        for message_id, message_data in messages:
            print(f"Processing message {message_id}: {message_data}")
            try:
                market_id_1 = message_data['market_id_1']
                platform_1 = PlatformType(message_data['platform_1'])
                market_id_2 = message_data['market_id_2']
                platform_2 = PlatformType(message_data['platform_2'])

                platform1_client = self.platforms.get(platform_1)
                platform2_client = self.platforms.get(platform_2)

                if not platform1_client or not platform2_client:
                    print(f"Platform client not found for one or both platforms in pair: {platform_1}, {platform_2}")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                orderbook1 = platform1_client.get_order_books([market_id_1])[0]
                orderbook2 = platform2_client.get_order_books([market_id_2])[0]

                if not orderbook1 or not orderbook2:
                    print(f"Could not fetch order book for one or both markets in pair: {market_id_1}, {market_id_2}")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue
                
                profit_threshold = float(os.getenv("PROFIT_THRESHOLD", 0.05))
                expected_slippage = float(os.getenv("EXPECTED_SLIPPAGE", 0.01))
                max_cost_str = os.getenv("MAX_TRADE_COST")
                max_cost = int(max_cost_str) if max_cost_str else None

                opportunity = calculate_cross_platform_arbitrage(
                    orderbook1, 
                    orderbook2,
                    profit_threshold=profit_threshold,
                    expected_slippage=expected_slippage,
                    max_cost=max_cost
                )

                if opportunity:
                    print(f"Arbitrage opportunity found for pair {market_id_1} and {market_id_2}: {opportunity}")
                    opportunity_message = {
                        "market_id_1": market_id_1,
                        "platform_1": platform_1.value,
                        "market_id_2": market_id_2,
                        "platform_2": platform_2.value,
                        "opportunity": str(opportunity)
                    }
                    self.redis_manager.add_to_stream(self.output_stream_name, opportunity_message)

                self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                print(f"Successfully processed and acknowledged message {message_id}.")

            except Exception as e:
                print(f"Error processing message {message_id}: {e}")

    def run(self):
        """
        Runs the arbitrage service indefinitely.
        """
        polling_interval = int(os.getenv("ARBITRAGE_POLLING_INTERVAL_S", 10))
        print(f"Starting Arbitrage Service with a {polling_interval} second interval...")
        while True:
            self.process_market_pairs()
            time.sleep(polling_interval)

if __name__ == '__main__':
    arbitrage_service = ArbitrageFinderService()
    arbitrage_service.run()
