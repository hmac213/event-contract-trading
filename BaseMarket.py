# import abstract class
from abc import ABC, abstractmethod
from typing import Any

class BaseMarket(ABC):
    @abstractmethod
    def get_order_books(self, market_ids: list[str]) -> list[dict[int, Any]]:
        """
        Arguments:
            Array Market_Ids: 
                - Array of Market IDs to get order books for.
            returns:
                - List of order books for the given market IDs.
        """
        pass

    @abstractmethod
    def get_markets(self, num_markets: int) -> list[str]:
        """
        Arguments:
            num_markets: 
                - Number of markets to return.
            returns:
                - List of market IDs.
        """
        pass
    