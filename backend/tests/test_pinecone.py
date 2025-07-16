import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import unittest
from dotenv import load_dotenv

from backend.core.Similarity import SimilarityManager
from backend.db.DBManager import DBManager
from backend.models.Market import Market
from backend.models.PlatformType import PlatformType

class TestPineconeDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        
        # Ensure all required environment variables are set
        required_vars = ["PINECONE_API_KEY", "OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
        for var in required_vars:
            if not os.getenv(var):
                raise EnvironmentError(f"Missing required environment variable: {var}. Please set it in your .env file.")

        cls.db_manager = DBManager()
        cls.similarity_manager = SimilarityManager(cls.db_manager)
        cls.initial_vector_count = cls.similarity_manager.index.describe_index_stats().get('total_vector_count', 0)
        
        cls.market1 = Market(
            platform=PlatformType.POLYMARKET,
            market_id="0x12345",
            name="Will Joe Biden win the 2024 US presidential election?",
            rules="This market will resolve to YES if Joe Biden wins the 2024 US presidential election.",
            close_timestamp=1730419200
        )
        
        cls.market2 = Market(
            platform=PlatformType.KALSHI,
            market_id="BIDEN2024",
            name="Joe Biden to win the 2024 U.S. presidential election",
            rules="The market resolves to Yes if Joseph R. Biden Jr. wins the 2024 U.S. Presidential election.",
            close_timestamp=1730419200
        )
        
        cls.test_markets = [cls.market1, cls.market2]
        cls.test_market_ids = [m.market_id for m in cls.test_markets]

    def test_a_add_markets(self):
        """
        Tests adding markets to the database and Pinecone index.
        Prefixed with 'a_' to ensure it runs first.
        """
        # Add to Supabase
        self.db_manager.add_markets(self.test_markets)
        
        # Add to Pinecone
        self.similarity_manager.add_markets_to_index(self.test_markets)
        
        # Wait for Pinecone to index the new vectors, polling for up-to-date stats
        import time
        max_wait_seconds = 120
        start_time = time.time()
        expected_count = self.initial_vector_count + 4  # 2 markets, 2 vectors each

        while time.time() - start_time < max_wait_seconds:
            stats = self.similarity_manager.index.describe_index_stats()
            current_count = stats.get('total_vector_count', 0)
            if current_count >= expected_count:
                break
            time.sleep(5)
        else:
            stats = self.similarity_manager.index.describe_index_stats()
            current_count = stats.get('total_vector_count', 0)
            self.fail(
                f"Pinecone index did not update in {max_wait_seconds}s. "
                f"Expected count >= {expected_count}, got {current_count}."
            )

    def test_b_find_similar_markets(self):
        """
        Tests finding a similar market from the Pinecone index.
        Prefixed with 'b_' to ensure it runs after adding.
        """
        similar_markets = self.similarity_manager.find_similar_markets(self.market1.market_id)
        
        self.assertIsNotNone(similar_markets)
        self.assertEqual(len(similar_markets), 1)
        self.assertEqual(similar_markets[0].market_id, self.market2.market_id)

    @classmethod
    def tearDownClass(cls):
        """
        Cleans up the created test data from Pinecone and Supabase.
        """
        # Cleanup from Pinecone
        pinecone_index = cls.similarity_manager.index
        pinecone_ids_to_delete = []
        for market in cls.test_markets:
            pinecone_ids_to_delete.append(f"{market.market_id}-name")
            pinecone_ids_to_delete.append(f"{market.market_id}-rule")
        
        if pinecone_ids_to_delete:
            pinecone_index.delete(ids=pinecone_ids_to_delete)

        # Cleanup from Supabase
        supabase_client = cls.db_manager.supabase
        if cls.test_market_ids:
            supabase_client.table("markets").delete().in_("market_id", cls.test_market_ids).execute()
        
        print("\nCleaned up test data from Pinecone and Supabase.")

if __name__ == "__main__":
    unittest.main() 