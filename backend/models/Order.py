from typing import Optional, Self
import uuid

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
        id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ):
        self.market_id = market_id
        self.side = side
        self.action = action
        self.order_type = order_type
        self.size = size
        self.price = price
        self.max_price = max_price
        self.id = id
        self.client_order_id = client_order_id if client_order_id else str(uuid.uuid4())

    @classmethod
    def create_limit_buy_order(
        cls, market_id: str, side: str, size: int, price: int
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
            price=price
        )

    @classmethod
    def create_limit_sell_order(
        cls, market_id: str, side: str, size: int, price: int
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
            price=price
        )

    @classmethod
    def create_market_buy_order(
        cls, market_id: str, side: str, size: int, max_price: int
    ) -> Self:
        """
        Factory for creating a market buy order.
        `max_price` is the max price per contract.
        """
        if max_price is None:
            raise ValueError("max_price must be provided for market buy orders.")
        return cls(
            market_id=market_id,
            side=side,
            action="buy",
            order_type="market",
            size=size,
            max_price=max_price
        )

    @classmethod
    def create_market_sell_order(
        cls, market_id: str, side: str, size: int
    ) -> Self:
        """Factory for creating a market sell order."""
        return cls(
            market_id=market_id,
            side=side,
            action="sell",
            order_type="market",
            size=size
        )