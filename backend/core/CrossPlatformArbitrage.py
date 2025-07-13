from backend.models.Orderbook import Orderbook
from typing import List, Tuple
import math


def calculate_cross_platform_arbitrage(ob1: Orderbook, ob2: Orderbook, profit_threshold: float, expected_slippage: float):
    """
    Arguments:
        orderbook: Orderbook -> Orderbook object for desired market (prices in tenths of cents)
        profit_threshold: float -> Minimum profit threshold for arbitrage opportunity
        expected_slippage: float -> Expected slippage for arbitrage opportunity
    Returns:
        number to buy at each: List[int] -> number to buy of each contract
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
        for i in range(len(levels[0])):
            price = levels[0][i]
            qty = levels[1][i]
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
            
    def max_shares(curve1: List[Tuple[int, int, int]], curve2: List[Tuple[int, int, int]]) -> int:
        lo = 1
        hi = min(curve1[-1][0], curve2[-1][0])
        best = 0

        while lo <= hi:
            mid = (hi + lo) // 2

            cost = cost_of_shares(mid, curve1) + cost_of_shares(mid, curve2)
            required_revenue = math.ceil(cost * (1 + expected_slippage) * (1 + profit_threshold))
            revenue = 1000 * mid

            if revenue >= required_revenue:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1

        return best
    
    size1 = max_shares(curve_y1, curve_n2)
    size2 = max_shares(curve_y2, curve_n1)

    # [yes1, no1, yes2, no2] -> take either (0, 2) or (1, 3)
    return [size1, size2, size1, size2]
