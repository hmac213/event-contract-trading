from backend.models.Market import Market
from collections import defaultdict
from openai import OpenAI
from pydantic import BaseModel
import os

class MarketPrediction(BaseModel):
    final_answer: bool

class Similarity:

    @staticmethod
    def check_similarity(new_markets: list[Market]) -> list[list[Market]]:
        # Group markets by platform
        platform_groups = defaultdict(list)
        for market in new_markets:
            platform_groups[market.platform.value].append(market)

        # Get all platforms
        platforms = list(platform_groups.keys())
        if len(platforms) < 2:
            return []  # Can't pair across platforms if only one exists

        # Create cross-platform pairings
        pairings = []
        # We'll zip across two platforms: the first two available with enough markets
        group1, group2 = platform_groups[platforms[0]], platform_groups[platforms[1]]

        for a_market in group1:
            for b_market in group2:

                if Similarity._check_GPT_similarity(a_market, b_market):
                    pairings.append([a_market, b_market])

        return pairings

    @staticmethod
    def _check_GPT_similarity(market1: Market, market2: Market) -> bool:
        client = OpenAI()
        completion = client.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are a helpful assistant whose job is to determine whether two event contract markets are IDENTICAL to each other."},
                {"role": "system", "content": "We define two event contracts to be IDENTICAL if and only if they track the same event outcome and resolve under the same rules."},
                {"role": "system", "content": "You may only establish two markets to be IDENTICAL if and only if you can determine with absolute certainty that the two markets meet the necessary criteria we outlined for IDENTICAL markets."},
                {"role": "system", "content": "If you deem the two markets to be IDENTICAL, you must return true and otherwise return false if there is even the slightest difference."},
                {"role": "user", "content": f"Are these two markets IDENTICAL? Market 1: {market1.name}, Rules: {market1.rules}. Market 2: {market2.name}, Rules: {market2.rules}."}
            ],
            response_format=MarketPrediction
        )
        prediction = completion.choices[0].message.parsed
        return prediction.final_answer

    