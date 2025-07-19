from typing import Optional
from models.OrderStatus import OrderStatus

class Trade:
    def __init__(
        self,
        order_id: str,
        quantity: int,
        price: int,
        executed_at: int,
        platform_trade_id: Optional[str] = None,
        id: Optional[str] = None,
    ):
        self.id = id
        self.order_id = order_id
        self.platform_trade_id = platform_trade_id
        self.quantity = quantity
        self.price = price
        self.executed_at = executed_at 