import time
import socket
import json
import os
import signal
import uuid
from cache.RedisManager import RedisManager
from db.DBManager import DBManager
from models.PlatformType import PlatformType
from models.OrderStatus import OrderStatus
from models.Order import Order
from models.Trade import Trade
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform
from services.mock_trade_executor.mock_db_manager import MockDBManager
from services.mock_trade_executor.strategies.mock_arbitrage_strategy import create_mock_arbitrage_orders

class MockTradeExecutionService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.mock_db_manager = MockDBManager()
        
        # Use REAL platforms for data collection - only trade execution is mocked
        self.platforms = {
            PlatformType.KALSHI: KalshiPlatform(),
            PlatformType.POLYMARKET: PolyMarketPlatform(),
        }

        self.input_stream_name = "arbitrage_opportunities_stream"
        self.group_name = "mock_trade_execution_group"
        self.consumer_name = f"mock-trade-executor-{socket.gethostname()}"
        
        self.redis_manager.create_consumer_group(self.input_stream_name, self.group_name)
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

        # Initialize mock balances with $50,000 for each platform
        self.mock_db_manager.initialize_mock_balances()

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Mock Trade Executor: Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def process_arbitrage_opportunities(self):
        """
        Processes arbitrage opportunities from the Redis Stream and executes MOCK trades.
        """
        print(f"Mock Trade Executor: Checking for new arbitrage opportunities as consumer '{self.consumer_name}'...")
        messages = self.redis_manager.read_from_stream(self.input_stream_name, self.group_name, self.consumer_name)
        
        if not messages:
            print("Mock Trade Executor: No new arbitrage opportunities.")
            return

        for message_id, message_data in messages:
            print(f"Mock Trade Executor: Processing message {message_id}: {message_data}")
            try:
                market_id_1 = message_data['market_id_1']
                platform_1 = PlatformType(message_data['platform_1'])
                market_id_2 = message_data['market_id_2']
                platform_2 = PlatformType(message_data['platform_2'])
                
                opportunity = json.loads(message_data['opportunity'].replace("'", "\""))

                # Get REAL market data (not mocked)
                market1 = self.db_manager.get_markets([market_id_1])[0]
                market2 = self.db_manager.get_markets([market_id_2])[0]
                
                platform1_client = self.platforms.get(platform_1)
                platform2_client = self.platforms.get(platform_2)

                if not all([market1, market2, platform1_client, platform2_client]):
                    print("Mock Trade Executor: Could not retrieve all necessary market or platform data. Skipping opportunity.")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                print(f"Mock Trade Executor: Executing MOCK arbitrage trade for opportunity: {opportunity}")
                
                # Check if we have sufficient mock balance
                if not self._check_mock_balance_sufficient(opportunity, platform_1, platform_2):
                    print("Mock Trade Executor: Insufficient mock balance for this arbitrage opportunity. Skipping.")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                create_mock_arbitrage_orders(
                    market1, market2, platform1_client, platform2_client, opportunity, self.mock_db_manager
                )
                
                self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                print(f"Mock Trade Executor: Successfully processed and acknowledged message {message_id}.")

            except Exception as e:
                print(f"Mock Trade Executor: Error processing message {message_id}: {e}")

    def _check_mock_balance_sufficient(self, opportunity: dict, platform_1: PlatformType, platform_2: PlatformType) -> bool:
        """
        Check if we have sufficient mock balance for the arbitrage opportunity.
        """
        total_shares = opportunity["shares"]
        max_price_1 = round(opportunity["max_price_1"] / 10)
        max_price_1 = max(1, min(max_price_1, 99))
        max_price_2 = round(opportunity["max_price_2"] / 10)
        max_price_2 = max(1, min(max_price_2, 99))

        # Calculate required balance (in cents)
        required_balance_1 = total_shares * max_price_1
        required_balance_2 = total_shares * max_price_2

        balance_1 = self.mock_db_manager.get_mock_balance(platform_1)
        balance_2 = self.mock_db_manager.get_mock_balance(platform_2)

        return balance_1 >= required_balance_1 and balance_2 >= required_balance_2

    def run(self):
        """
        Runs the mock trade execution service indefinitely.
        """
        polling_interval = int(os.getenv("MOCK_TRADE_POLLING_INTERVAL_S", 10))
        print(f"Starting Mock Trade Execution Service with a {polling_interval} second interval...")
        print("🎭 MOCK MODE: All trades will be simulated, no real money will be used!")
        print("💰 Starting with $50,000 mock balance on each platform")
        
        # Print initial balances
        kalshi_balance = self.mock_db_manager.get_mock_balance(PlatformType.KALSHI)
        polymarket_balance = self.mock_db_manager.get_mock_balance(PlatformType.POLYMARKET)
        print(f"📊 Mock Balances: Kalshi=${kalshi_balance/100:.2f}, PolyMarket=${polymarket_balance/100:.2f}")
        
        while not self.shutdown_requested:
            self.process_arbitrage_opportunities()
            if not self.shutdown_requested:
                time.sleep(polling_interval)
        print("Mock Trade Execution Service shut down gracefully.")

if __name__ == '__main__':
    mock_trade_execution_service = MockTradeExecutionService()
    mock_trade_execution_service.run()
