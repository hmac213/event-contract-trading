import time
import socket
import os
from backend.core.Similarity import SimilarityManager
from cache.RedisManager import RedisManager
from db.DBManager import DBManager
from models.Market import Market
from models.PlatformType import PlatformType

class MarketSimilarityService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.similarity_manager = SimilarityManager(self.db_manager)
        
        self.input_stream_name = "market_events_stream"
        self.output_stream_name = "similar_market_pairs_stream"
        self.group_name = "similarity_group"
        # Use hostname to create a unique consumer name for this instance
        self.consumer_name = f"similarity-consumer-{socket.gethostname()}"

        # Ensure the consumer group exists
        self.redis_manager.create_consumer_group(self.input_stream_name, self.group_name)

    def process_market_events(self):
        """
        Processes market events from the Redis Stream.
        """
        print(f"Checking for new market events as consumer '{self.consumer_name}'...")
        messages = self.redis_manager.read_from_stream(self.input_stream_name, self.group_name, self.consumer_name)
        
        if not messages:
            print("No new market events.")
            return

        for message_id, message_data in messages:
            print(f"Processing message {message_id}: {message_data}")
            try:
                # Reconstruct the market object from the message data
                market = Market(
                    market_id=message_data['market_id'],
                    platform=PlatformType(message_data['platform']),
                    name=message_data['name'],
                    rules=message_data['rules']
                )

                # Add the market to the database if it's not already there
                if not self.db_manager.get_markets([market.market_id]):
                     self.db_manager.add_markets([market])

                # Find similar markets
                similar_markets = self.similarity_manager.find_similar_markets(market.market_id)

                if similar_markets:
                    print(f"Found {len(similar_markets)} similar markets for {market.market_id}")
                    all_pairings = []
                    for similar_market in similar_markets:
                        market_info_1 = {'market_id': market.market_id, 'platform': market.platform.value}
                        market_info_2 = {'market_id': similar_market.market_id, 'platform': similar_market.platform.value}
                        
                        # Sort by market_id to ensure uniqueness, making the pair tuple hashable
                        if market_info_1['market_id'] > market_info_2['market_id']:
                            market_info_1, market_info_2 = market_info_2, market_info_1

                        pair_tuple = (
                            (market_info_1['market_id'], market_info_1['platform']),
                            (market_info_2['market_id'], market_info_2['platform'])
                        )
                        all_pairings.append(pair_tuple)

                    unique_pairings = list(set(all_pairings))
                    if unique_pairings:
                        # For the database, we only need the market IDs
                        db_pairs = [(p[0][0], p[1][0]) for p in unique_pairings]
                        self.db_manager.add_market_pairs(db_pairs)

                        for market1_info, market2_info in unique_pairings:
                            pair_message = {
                                "market_id_1": market1_info[0],
                                "platform_1": market1_info[1],
                                "market_id_2": market2_info[0],
                                "platform_2": market2_info[1]
                            }
                            self.redis_manager.add_to_stream(self.output_stream_name, pair_message)
                        print(f"Published {len(unique_pairings)} new market pairs.")

                # Acknowledge the message was processed successfully
                self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                print(f"Successfully processed and acknowledged message {message_id}.")

            except Exception as e:
                print(f"Error processing message {message_id}: {e}")
                # We do not acknowledge the message, so it can be re-processed.

    def run(self):
        """
        Runs the similarity service indefinitely.
        """
        polling_interval = int(os.getenv("SIMILARITY_POLLING_INTERVAL_S", 10))
        print(f"Starting Market Similarity Service with a {polling_interval} second interval...")
        while True:
            self.process_market_events()
            time.sleep(polling_interval)

if __name__ == '__main__':
    similarity_service = MarketSimilarityService()
    similarity_service.run()
