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
from utils.startup_coordinator import StartupCoordinator


class MarketPrediction(BaseModel):
    final_answer: bool


class MarketSimilarityService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.similarity_db_manager = SimilarityDBManager()
        self.startup_coordinator = StartupCoordinator()
        
        self.input_stream_name = "market_events_stream"
        self.output_stream_name = "similar_market_pairs_stream"
        self.group_name = "similarity_group"
        self.consumer_name = f"similarity-consumer-{socket.gethostname()}"

        self.redis_manager.create_consumer_group(self.input_stream_name, self.group_name)
        self.client = instructor.patch(OpenAI())
        self.shutdown_requested = False
        
        # Track already-compared market pairs to avoid duplicates
        self.compared_pairs = set()
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def _get_canonical_pair(self, market1_id: str, market2_id: str) -> tuple:
        """Get canonical ordering of market pair for deduplication."""
        return tuple(sorted([market1_id, market2_id]))

    def _already_compared(self, market1_id: str, market2_id: str) -> bool:
        """Check if this market pair has already been compared."""
        pair = self._get_canonical_pair(market1_id, market2_id)
        return pair in self.compared_pairs

    def _mark_compared(self, market1_id: str, market2_id: str) -> None:
        """Mark this market pair as already compared."""
        pair = self._get_canonical_pair(market1_id, market2_id)
        self.compared_pairs.add(pair)

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
                # Validate required fields
                required_fields = ['market_id', 'platform', 'name', 'rules']
                missing_fields = [field for field in required_fields if field not in message_data]
                
                if missing_fields:
                    print(f"⚠️ Skipping message {message_id}: Missing required fields: {missing_fields}")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue
                
                # Use robust Market creation from stream data
                market = Market.from_stream_data(message_data)
                print(f"✅ Successfully created market: {market.market_id}")

                # Market should already be in DB from market_poller, but check just in case
                existing_markets = self.db_manager.get_markets([market.market_id])
                if not existing_markets:
                    print(f"⚠️ Market {market.market_id} not found in DB, this shouldn't happen")
                    continue
                
                self.similarity_db_manager.add_markets_to_index([market])

                candidate_market_ids = self.similarity_db_manager.find_similar_markets(market, self.similarity_threshold)
                
                if not candidate_market_ids:
                    print(f"🔍 No similar markets found above threshold {self.similarity_threshold} for {market.market_id}")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                # Filter out already-compared pairs
                new_candidate_ids = []
                skipped_count = 0
                for candidate_id in candidate_market_ids:
                    if not self._already_compared(market.market_id, candidate_id):
                        new_candidate_ids.append(candidate_id)
                    else:
                        skipped_count += 1

                if skipped_count > 0:
                    print(f"⏭️ Skipped {skipped_count} already-compared pairs for {market.market_id}")

                if not new_candidate_ids:
                    print(f"🔄 All candidates for {market.market_id} already compared")
                    self.redis_manager.acknowledge_message(self.input_stream_name, self.group_name, message_id)
                    continue

                candidate_markets = self.db_manager.get_markets(new_candidate_ids)
                print(f"🧠 Running GPT verification on {len(candidate_markets)} new pairs for {market.market_id}")

                identical_markets = []
                for candidate_market in candidate_markets:
                    # Mark this pair as compared regardless of result
                    self._mark_compared(market.market_id, candidate_market.market_id)
                    
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
        Runs the similarity service with startup coordination.
        """
        polling_interval = int(os.getenv("SIMILARITY_POLLING_INTERVAL_S", 10))
        wait_for_market_poller = os.getenv("WAIT_FOR_MARKET_POLLER", "true").lower() == "true"
        
        print(f"🚀 Starting Market Similarity Service...")
        print(f"⏰ Polling interval: {polling_interval}s")
        print(f"🎯 Wait for market poller: {wait_for_market_poller}")
        print(f"📊 Similarity threshold: {self.similarity_threshold}")
        print(f"🚀 Optimizations: Duplicate tracking enabled, threshold filtering enabled")
        
        self.startup_coordinator.set_startup_phase("market_similarity", "initializing")
        
        try:
            # Wait for market poller to complete initial load
            if wait_for_market_poller:
                print("⏳ Waiting for market poller to complete initial data load...")
                if self.startup_coordinator.wait_for_initial_load("market_poller", timeout=600):
                    print("✅ Market poller initial load complete, starting similarity processing")
                else:
                    print("⚠️ Timeout waiting for market poller, proceeding anyway")
            
            # Signal ready and start processing
            self.startup_coordinator.signal_service_ready("market_similarity")
            print("🔄 Starting market similarity processing...")
            
            while not self.shutdown_requested:
                self.process_market_events()
                if not self.shutdown_requested:
                    time.sleep(polling_interval)
                    
        except Exception as e:
            print(f"❌ Fatal error in market similarity service: {e}")
            self.startup_coordinator.set_startup_phase("market_similarity", "failed")
            raise
                    
        print("Market Similarity Service shut down gracefully.")

if __name__ == '__main__':
    similarity_service = MarketSimilarityService()
    similarity_service.run()
