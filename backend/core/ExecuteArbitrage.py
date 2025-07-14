from backend.models.Order import Order
from backend.models.PlatformType import PlatformType
from backend.platform.BasePlatform import BasePlatform

class ExecuteArbitrage():

    @staticmethod
    def place_arbitrage_orders(platform1: BasePlatform, platform2: BasePlatform, opportunity: dict) -> None:
        if opportunity["type"] == "yes1_no2":
            order1 = Order.create_market_order(opportunity["shares"], opportunity["total_cost"], platform1, "yes")
            order2 = Order.create_market_order(opportunity["shares"], opportunity["total_cost"], platform2, "no")
        elif opportunity["type"] == "yes2_no1":
            order1 = Order.create_market_order(opportunity["shares"], opportunity["total_cost"], platform1, "no")
            order2 = Order.create_market_order(opportunity["shares"], opportunity["total_cost"], platform2, "yes")
        else:
            raise ValueError(f"Invalid opportunity type: {opportunity['type']}")
        
        platform1.place_order(order1)
        platform2.place_order(order2)

    