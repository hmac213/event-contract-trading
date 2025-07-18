import time
import socket
import json
import os
import signal
from cache.RedisManager import RedisManager
from db.DBManager import DBManager
from models.PlatformType import PlatformType
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform
from services.trade_executor.strategies.arbitrage_strategy import create_arbitrage_orders

class TradeExecutionService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.platforms = {
            PlatformType.KALSHI: KalshiPlatform(),
            PlatformType.POLYMARKET: PolyMarketPlatform(),
        }

        self.input_stream_name = "arbitrage_opportunities_stream"
        self.group_name = "trade_execution_group"
        self.consumer_name = f"trade-executor-{socket.gethostname()}"
        
        self.redis_manager.create_consumer_group(self.input_stream_name, self.group_name)
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def process_arbitrage_opportunities(self):
        """
        Processes arbitrage opportunities from the Redis Stream and executes trades.
        """
        print(f"Checking for new arbitrage opportunities as consumer '{self.consumer_name}'...")
        messages = self.redis_manager.read_from_stream(self.input_stream_name, self.group_name, self.consumer_name)
        
        if not messages:
            print("No new arbitrage opportunities.")
            return

        for message_id, message_data in messages:
            print(f"Processing message {message_id}: {message_data}")
            try:
                market_id_1 = message_data['market_id_1']
                platform_1 = PlatformType(message_data['platform_1'])
                market_id_2 = message_data['market_id_2']
                platform_2 = PlatformType(message_data['platform_2'])
                
                opportunity = json.loads(message_data['opportunity'].replace("'", "\""))

                market1 = self.db_manager.get_markets([market_id_1])[0]
                market2 = self.db_manager.get_markets([market_id_2])[0]
                
                platform1_client = self.platforms.get(platform_1)
                platform2_client = self.platforms.get(platform_2)

                if not all([market1, market2, platform1_client, platform2_client]):
                    print("Could not retrieve all necessary market or platform data. Skipping opportunity.")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                print(f"Executing arbitrage trade for opportunity: {opportunity}")
                create_arbitrage_orders(
                    market1, market2, platform1_client, platform2_client, opportunity, self.db_manager
                )
                
                self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                print(f"Successfully processed and acknowledged message {message_id}.")

            except Exception as e:
                print(f"Error processing message {message_id}: {e}")

    def run(self):
        """
        Runs the trade execution service indefinitely.
        """
        polling_interval = int(os.getenv("TRADE_POLLING_INTERVAL_S", 10))
        print(f"Starting Trade Execution Service with a {polling_interval} second interval...")
        while not self.shutdown_requested:
            self.process_arbitrage_opportunities()
            if not self.shutdown_requested:
                time.sleep(polling_interval)
        print("Trade Execution Service shut down gracefully.")

if __name__ == '__main__':
    trade_execution_service = TradeExecutionService()
    trade_execution_service.run()
