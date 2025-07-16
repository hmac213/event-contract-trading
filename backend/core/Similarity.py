import instructor
import numpy as np
import os
import pinecone
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List
from openai import OpenAI

from backend.db.DBManager import DBManager
from backend.models.Market import Market


class MarketPrediction(BaseModel):
    final_answer: bool


class SimilarityManager:
    def __init__(self, db_manager: DBManager):
        self.model = SentenceTransformer("intfloat/multilingual-e5-large")
        self.embedding_dimension = 1024

        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set.")

        self.pinecone = pinecone.Pinecone(api_key=pinecone_api_key, model=self.model)
        self.index_name = "event-contract-markets"

        if self.index_name not in self.pinecone.list_indexes().names():
            self.pinecone.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=pinecone.ServerlessSpec(cloud='aws', region='us-east-1')
            )
        self.index = self.pinecone.Index(self.index_name)

        self.client = instructor.patch(OpenAI())
        self.db_manager = db_manager

    def _embed_sentences(self, sentences: List[str]) -> np.ndarray:
        embeddings = self.model.encode(
            sentences,
            batch_size=16,
            convert_to_numpy=True
        )
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

    def add_markets_to_index(self, markets: List[Market]):
        vectors_to_upsert = []
        for market in markets:
            name_embedding, rules_embedding = self._embed_sentences([market.name, market.rules])

            vectors_to_upsert.append({
                "id": f"{market.market_id}-name",
                "values": name_embedding.tolist(),
                "metadata": {"market_id": str(market.market_id), "platform": market.platform.value, "type": "name"}
            })
            vectors_to_upsert.append({
                "id": f"{market.market_id}-rule",
                "values": rules_embedding.tolist(),
                "metadata": {"market_id": str(market.market_id), "platform": market.platform.value, "type": "rule"}
            })
        
        if vectors_to_upsert:
            for i in range(0, len(vectors_to_upsert), 100):
                batch = vectors_to_upsert[i:i+100]
                self.index.upsert(vectors=batch)

    def find_similar_markets(self, market_id: str) -> List[Market]:
        markets = self.db_manager.get_markets([market_id])
        if not markets:
            return []
        market = markets[0]

        market_name_embedding = self._embed_sentences([market.name])[0]

        query_response = self.index.query(
            vector=market_name_embedding.tolist(),
            top_k=3,
            filter={
                "platform": {"$ne": market.platform.value},
                "type": "name"
            },
            include_metadata=True
        )

        candidate_market_ids = [match['metadata']['market_id'] for match in query_response['matches']]
        
        if not candidate_market_ids:
            return []

        candidate_markets = self.db_manager.get_markets(candidate_market_ids)

        identical_markets = []
        for candidate_market in candidate_markets:
            if self._check_GPT_similarity(market, candidate_market):
                identical_markets.append(candidate_market)

        return identical_markets

    def _check_GPT_similarity(self, market1: Market, market2: Market) -> bool:
        try:
            prediction: MarketPrediction = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
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

    