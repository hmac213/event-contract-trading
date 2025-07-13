# import abstract class
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from backend.models.Order import Order

if TYPE_CHECKING:
    from backend.models.Market import Market
    from backend.models.Orderbook import Orderbook
    
class BasePlatform(ABC):
    @abstractmethod
    def get_order_books(self, market_ids: list[str]) -> list["Orderbook"]:
        """
        Arguments:
            Array Market_Ids: 
                - Array of Market IDs to get order books for.
            returns:
                - List of order books for the given market IDs.
        """
        pass

    @abstractmethod
    def find_new_markets(self, num_markets: int) -> list[str]:
        """
        Arguments:
            num_markets: 
                - Number of markets to return.
            returns:
                - List of market IDs.
        We want to find new markets here that we will then check to see if they are valid.
        """
        pass

    @abstractmethod
    def get_markets(self, market_ids: list[str]) -> list["Market"]:
        """
        Arguments:
            market_ids: 
                - list of Market ID to get the market for.
            returns:
                - Market object for the given market ID.
        """
        pass

    @abstractmethod
    def place_order(self, order: Order) -> dict:
        pass

    @abstractmethod
    def cancel_order(self, order: Order):
        pass