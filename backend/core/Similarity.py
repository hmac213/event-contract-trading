from backend.models.Market import Market
from collections import defaultdict

class Similarity:

    @staticmethod
    def check_similarity(new_markets: list[Market]) -> list[list[Market]]:
        if not new_markets:
            return []

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
        p1, p2 = platforms[0], platforms[1]
        group1, group2 = platform_groups[p1], platform_groups[p2]

        min_len = min(len(group1), len(group2))
        for i in range(min_len):
            pairings.append([group1[i], group2[i]])

    
        return []