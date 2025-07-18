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

    def find_similar_markets(self, market: Market) -> List[str]:
        query_response = self.index.search(
            namespace="__default__",
            query={
                "inputs": {"text": market.name},
                "top_k": 3,
                "filter": {
                    "platform": {"$ne": market.platform.value},
                    "type": "name"
                },
            },
            fields=["market_id"]
        )

        return [match['fields']['market_id'] for match in query_response['result']['hits'] if 'market_id' in match['fields']]
