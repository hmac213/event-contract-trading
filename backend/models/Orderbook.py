
class Orderbook():
    def __init__(self, market_id: str, timestamp: int, yes: dict["str", list[list[int]]], no: dict["str", list[list[int]]]):
        self.market_id = market_id
        self.timestamp = timestamp
        self.yes = yes
        self.no = no
        