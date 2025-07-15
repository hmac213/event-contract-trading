from backend.models.Orderbook import Orderbook
from typing import List, Tuple, Optional, Dict, Any
import math


def calculate_cross_platform_arbitrage(
    ob1: Orderbook,
    ob2: Orderbook,
    profit_threshold: Optional[float] = 0.05,
    expected_slippage: Optional[float] = 0.01,
    max_cost: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Arguments:
        ob1: Orderbook -> Orderbook for the first platform
        ob2: Orderbook -> Orderbook for the second platform
        profit_threshold: float -> Minimum profit threshold for arbitrage opportunity
        expected_slippage: float -> Expected slippage for arbitrage opportunity
        max_cost: int -> Maximum cost willing to incur across both markets
    Returns:
        The best arbitrage opportunity as a dictionary, or None if no opportunity is found.
    """

    # IMPORTANT: ASSUMES MANUAL NON-DECREASING ORDERBOOKS
    yes1 = ob1.yes["ask"]
    no1 = ob1.no["ask"]
    yes2 = ob2.yes["ask"]
    no2 = ob2.no["ask"]

    def build_curve(levels: List[List[int]]) -> List[Tuple[int, int, int]]:
        cumulative = []
        total_qty = 0
        total_cost = 0
        for price, qty in levels:
            total_qty += qty
            total_cost += price * qty
            cumulative.append((total_qty, total_cost, price))
        return cumulative
    
    curve_y1 = build_curve(yes1)
    curve_n1 = build_curve(no1)
    curve_y2 = build_curve(yes2)
    curve_n2 = build_curve(no2)

    def cost_of_shares(X: int, curve: List[Tuple[int, int, int]]) -> int:
        for q, c, p in curve:
            if q >= X:
                dif = q - X
                cost_dif = p * dif
                return c - cost_dif
        return float("inf")

    def price_of_share(X: int, curve: List[Tuple[int, int, int]]) -> int:
        """Gets the price of the X-th share in a cumulative curve."""
        last_qty = 0
        for q, _, p in curve:
            if last_qty < X <= q:
                return p
            last_qty = q
        return float("inf")
            
    def get_arbitrage_details(curve1: List[Tuple[int, int, int]], curve2: List[Tuple[int, int, int]]) -> Tuple[int, int, int, int]:
        lo = 1
        hi = min(curve1[-1][0], curve2[-1][0])
        best_profit_shares = 0

        while lo <= hi:
            mid = (hi + lo) // 2
            
            # Clamp shares if marginal price is >= $1.00
            price1 = price_of_share(mid, curve1)
            price2 = price_of_share(mid, curve2)
            if price1 + price2 >= 1000:
                hi = mid - 1
                continue

            cost = cost_of_shares(mid, curve1) + cost_of_shares(mid, curve2)
            required_revenue = math.ceil(cost * (1 + expected_slippage) * (1 + profit_threshold))
            revenue = 1000 * mid

            if revenue >= required_revenue:
                best_profit_shares = mid
                lo = mid + 1
            else:
                hi = mid - 1
        
        best_cost_shares = float('inf')
        if max_cost is not None:
            lo, hi, best_cost_shares = 1, min(curve1[-1][0], curve2[-1][0]), 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if cost_of_shares(mid, curve1) + cost_of_shares(mid, curve2) <= max_cost:
                    best_cost_shares = mid
                    lo = mid + 1
                else:
                    hi = mid - 1

        final_shares = min(best_profit_shares, best_cost_shares)
        total_cost = cost_of_shares(final_shares, curve1) + cost_of_shares(final_shares, curve2) if final_shares > 0 else 0
        
        max_price1 = price_of_share(final_shares, curve1) if final_shares > 0 else 0
        max_price2 = price_of_share(final_shares, curve2) if final_shares > 0 else 0
        return final_shares, total_cost, max_price1, max_price2
    
    shares1, cost1, max_p_y1, max_p_n2 = get_arbitrage_details(curve_y1, curve_n2)
    shares2, cost2, max_p_y2, max_p_n1 = get_arbitrage_details(curve_y2, curve_n1)

    opp1 = None
    if shares1 > 0:
        opp1 = {
            "type": "yes1_no2",
            "shares": shares1,
            "total_cost": cost1,
            "cost_per_share": cost1 / shares1,
            "max_price_1": max_p_y1,
            "max_price_2": max_p_n2,
        }

    opp2 = None
    if shares2 > 0:
        opp2 = {
            "type": "yes2_no1",
            "shares": shares2,
            "total_cost": cost2,
            "cost_per_share": cost2 / shares2,
            "max_price_1": max_p_y2,
            "max_price_2": max_p_n1,
        }

    if opp1 and opp2:
        return opp1 if opp1["cost_per_share"] <= opp2["cost_per_share"] else opp2

    return opp1 or opp2
