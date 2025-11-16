import os
import pinecone
from typing import List
from models.Market import Market

class SimilarityDBManager:
    def __init__(self):
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set.")

        self.pinecone = pinecone.Pinecone(api_key=pinecone_api_key)
        self.index_name = "event-contract-markets"

        if self.index_name not in self.pinecone.list_indexes().names():
            self.pinecone.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed= {
                    "model": "multilingual-e5-large",
                    "field_map": {
                        "text": "text"
                    }
                }
            )
        self.index = self.pinecone.Index(self.index_name)

    def add_markets_to_index(self, markets: List[Market]):
        records_to_upsert = []
        for market in markets:
            records_to_upsert.append({
                "id": f"{market.market_id}-name",
                "text": market.name,
                "market_id": str(market.market_id),
                "platform": market.platform.value,
                "type": "name"
            })
            records_to_upsert.append({
                "id": f"{market.market_id}-rule",
                "text": market.rules,
                "market_id": str(market.market_id),
                "platform": market.platform.value,
                "type": "rule"
            })
        
        if records_to_upsert:
            for i in range(0, len(records_to_upsert), 100):
                batch = records_to_upsert[i:i+100]
                self.index.upsert_records(records=batch, namespace="__default__")

    def find_similar_markets(self, market: Market, similarity_threshold: float = 0.7) -> List[str]:
        """
        Find similar markets using vector similarity search.
        
        Args:
            market: The market to find similarities for
            similarity_threshold: Minimum similarity score (0.0-1.0) to consider a match
        
        Returns:
            List of market IDs that are similar enough to warrant GPT verification
        """
        query_response = self.index.search(
            namespace="__default__",
            query={
                "inputs": {"text": market.name},
                "top_k": 10,  # Get more candidates to filter by threshold
                "filter": {
                    "platform": {"$ne": market.platform.value},
                    "type": "name"
                },
            },
            fields=["market_id"]
        )

        # Filter results by similarity threshold and limit to top 3
        similar_markets = []
        for match in query_response['result']['hits']:
            if 'market_id' in match['fields'] and match['score'] >= similarity_threshold:
                similar_markets.append(match['fields']['market_id'])
                if len(similar_markets) >= 3:  # Still limit to max 3 for GPT efficiency
                    break
        
        print(f"🔍 Vector search found {len(query_response['result']['hits'])} candidates, "
              f"{len(similar_markets)} above threshold {similarity_threshold}")
        
        return similar_markets
