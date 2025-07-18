from typing import Optional, Self
import uuid
from models.OrderStatus import OrderStatus

class Order:
    def __init__(
        self,
        market_id: str,
        side: str,
        action: str,
        order_type: str,
        size: int,
        price: Optional[int] = None,
        max_price: Optional[int] = None,
        time_in_force: Optional[str] = 'GTC',
        id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        status: Optional[OrderStatus] = OrderStatus.PENDING,
        order_id: Optional[str] = None, # platform specific order id
        fill_size: Optional[int] = 0,
    ):
        self.market_id = market_id
        self.side = side
        self.action = action
        self.order_type = order_type
        self.size = size
        self.price = price
        self.max_price = max_price
        self.time_in_force = time_in_force # GTC, IOC, FOK
        self.id = id
        self.client_order_id = client_order_id if client_order_id else str(uuid.uuid4())
        self.status = status
        self.order_id = order_id
        self.fill_size = fill_size

    @classmethod
    def create_limit_buy_order(
        cls, market_id: str, side: str, size: int, price: int, time_in_force: str = 'GTC'
    ) -> Self:
        """Factory for creating a limit buy order."""
        if not (0 < price < 100):
            raise ValueError("Price for a limit order must be between 1 and 99 cents.")
        return cls(
            market_id=market_id,
            side=side,
            action="buy",
            order_type="limit",
            size=size,
            price=price,
            time_in_force=time_in_force
        )

    @classmethod
    def create_limit_sell_order(
        cls, market_id: str, side: str, size: int, price: int, time_in_force: str = 'GTC'
    ) -> Self:
        """Factory for creating a limit sell order."""
        if not (0 < price < 100):
            raise ValueError("Price for a limit order must be between 1 and 99 cents.")
        return cls(
            market_id=market_id,
            side=side,
            action="sell",
            order_type="limit",
            size=size,
            price=price,
            time_in_force=time_in_force
        )

    @classmethod
    def create_market_buy_order(
        cls, market_id: str, side: str, size: int, max_price: int, time_in_force: str = 'IOC'
    ) -> Self:
        """
        Factory for creating a market buy order.
        `max_price` is the max price per contract.
        """
        if max_price is None or not (0 < max_price <= 100):
            raise ValueError("max_price for a market buy order must be between 1 and 100 cents.")
        return cls(
            market_id=market_id,
            side=side,
            action="buy",
            order_type="market",
            size=size,
            max_price=max_price,
            time_in_force=time_in_force
        )

    @classmethod
    def create_market_sell_order(
        cls, market_id: str, side: str, size: int, time_in_force: str = 'IOC'
    ) -> Self:
        """Factory for creating a market sell order."""
        return cls(
            market_id=market_id,
            side=side,
            action="sell",
            order_type="market",
            size=size,
            time_in_force=time_in_force
        )