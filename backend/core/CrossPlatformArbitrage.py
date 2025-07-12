from backend.models.Orderbook import Orderbook
from typing import List, Tuple


def calculate_cross_platform_arbitrage(ob1: Orderbook, ob2: Orderbook, profit_threshold: float, expected_slippage: float):
    """
    Arguments:
        orderbook: Orderbook -> Orderbook object for desired market (prices in cents)
        profit_threshold: float -> Minimum profit threshold for arbitrage opportunity
        expected_slippage: float -> Expected slippage for arbitrage opportunity
    Returns:
        
    """

    # IMPORTANT: ASSUMES MANUAL NON-DECREASING ORDERBOOKS
    yes1 = ob1.yes["ask"]
    no1 = ob1.no["ask"]
    yes2 = ob2.yes["ask"]
    no2 = ob2.no["ask"]

    def build_curve(levels: List[List[int]]) -> List[Tuple[int]]:
        cumulative = []
        total_qty = 0
        total_cost = 0
        for price, qty in levels:
            total_qty += qty
            total_price += price
            cumulative.append((total_qty, total_cost))
        return cumulative
    
    curve_y1 = build_curve(yes1)
    curve_n1 = build_curve(no1)
    curve_y2 = build_curve(yes2)
    curve_n2 = build_curve(no2)

    def cost_of_shares(X: int, curve: List[Tuple[int]]) -> int:
        for q, c in curve:
            if q >= X:
                dif = q - X
                cost_dif = c * dif
                return c - cost_dif
            
    def max_shares(curve1, curve2):
        lo = 0
        hi = min(curve1[-1][0], curve2[-1][0])
        best = 0

        while lo <= hi:
            mid = (lo + hi) // 2
            if mid == 0:
                lo = 1
                continue

            cost = cost_of_shares(mid, curve1) + cost_of_shares(mid, curve2)
            revenue = 1000 * mid

            if revenue >= cost * (1 + profit_threshold):
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1

        return best * 
