import time
import socket
import os
import instructor
import signal
from openai import OpenAI
from pydantic import BaseModel
from typing import List

from cache.RedisManager import RedisManager
from db.DBManager import DBManager
from models.Market import Market
from models.PlatformType import PlatformType
from services.market_similarity.db.pinecone_manager import SimilarityDBManager


class MarketPrediction(BaseModel):
    final_answer: bool


class MarketSimilarityService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.similarity_db_manager = SimilarityDBManager()
        
        self.input_stream_name = "market_events_stream"
        self.output_stream_name = "similar_market_pairs_stream"
        self.group_name = "similarity_group"
        self.consumer_name = f"similarity-consumer-{socket.gethostname()}"

        self.redis_manager.create_consumer_group(self.input_stream_name, self.group_name)
        self.client = instructor.patch(OpenAI())
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def _check_gpt_similarity(self, market1: Market, market2: Market) -> bool:
        try:
            model_name = os.getenv("GPT_MODEL_NAME", "gpt-4o-2024-08-06")
            prediction: MarketPrediction = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant whose job is to determine whether two event contract markets are IDENTICAL to each other."},
                    {"role": "system", "content": "We define two event contracts to be IDENTICAL if and only if they track the same event outcome and resolve under the same rules."},
                    {"role": "system", "content": "You may only establish two markets to be IDENTICAL if and only if you can determine with absolute certainty that the two markets meet the necessary criteria we outlined for IDENTICAL markets."},
                    {"role": "system", "content": "If you deem the two markets to be IDENTICAL, you must return true and otherwise return false if there is even the slightest difference."},
                    {"role": "user", "content": f"Are these two markets IDENTICAL? Market 1: {market1.name}, Rules: {market1.rules}. Market 2: {market2.name}, Rules: {market2.rules}."}
                ],
                response_model=MarketPrediction
            )
            return prediction.final_answer
        except Exception as e:
            print(f"An error occurred during GPT similarity check: {e}")
            return False

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
                message_data['platform'] = PlatformType(message_data['platform'])
                market = Market(**message_data)

                if not self.db_manager.get_markets([market.market_id]):
                     self.db_manager.add_markets([market])
                
                self.similarity_db_manager.add_markets_to_index([market])

                candidate_market_ids = self.similarity_db_manager.find_similar_markets(market)
                
                if not candidate_market_ids:
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                candidate_markets = self.db_manager.get_markets(candidate_market_ids)

                identical_markets = []
                for candidate_market in candidate_markets:
                    if self._check_gpt_similarity(market, candidate_market):
                        identical_markets.append(candidate_market)

                if identical_markets:
                    print(f"Found {len(identical_markets)} similar markets for {market.market_id}")
                    all_pairings = []
                    for similar_market in identical_markets:
                        market_info_1 = {'market_id': market.market_id, 'platform': market.platform.value}
                        market_info_2 = {'market_id': similar_market.market_id, 'platform': similar_market.platform.value}
                        
                        if market_info_1['market_id'] > market_info_2['market_id']:
                            market_info_1, market_info_2 = market_info_2, market_info_1

                        pair_tuple = (
                            (market_info_1['market_id'], market_info_1['platform']),
                            (market_info_2['market_id'], market_info_2['platform'])
                        )
                        all_pairings.append(pair_tuple)

                    unique_pairings = list(set(all_pairings))
                    if unique_pairings:
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
        while not self.shutdown_requested:
            self.process_market_events()
            if not self.shutdown_requested:
                time.sleep(polling_interval)
        print("Market Similarity Service shut down gracefully.")

if __name__ == '__main__':
    similarity_service = MarketSimilarityService()
    similarity_service.run()
