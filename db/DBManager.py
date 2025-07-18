from models.PlatformType import PlatformType
from models.Market import Market
from models.Order import Order
from models.Trade import Trade
from models.OrderStatus import OrderStatus
from models.Orderbook import Orderbook
from supabase import create_client
import os
import math
import logging
from postgrest.exceptions import APIError

class DBManager():
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)


   
    def add_market_pairs(self, market_pairs: list[list[Market]]) -> None:
        sql_pairs = []
        for pair in market_pairs:
            if len(pair) != 2:
                continue  # skip incomplete or malformed pairs

            m1, m2 = pair[0], pair[1]
            id1, id2 = m1.market_id, m2.market_id

            # Enforce order to satisfy CHECK constraint: market_id_1 < market_id_2
            if id1 < id2:
                sql_pairs.append({"market_id_1": id1, "market_id_2": id2})
            else:
                sql_pairs.append({"market_id_1": id2, "market_id_2": id1})

        if not sql_pairs:
            return

        try:
            self.supabase.table("market_pairs").insert(sql_pairs).execute()
        except APIError as e:
            if e.code == '23505':  # Unique constraint violation
                logging.debug(f"Duplicate market pair insertion ignored: {e}")
            else:
                logging.debug(f"Failed to insert market pairs: {e}")


    def get_all_market_pairs(self) -> list[list[str]]:
        """
        Returns all market pairs from the database.
        Each pair is a list of two market IDs.
        """
        response = self.supabase.table("market_pairs").select("market_id_1, market_id_2").execute()
        if response.data:
            return [[row["market_id_1"], row["market_id_2"]] for row in response.data]
        return []
    
    def add_markets(self, markets: list[Market], chunk_size: int = 100) -> None:
        # Convert Market objects to dictionaries
        sql_markets = []
        market_ids = []

        for m in markets:
            sql_markets.append({
                "platform": m.platform.value,
                "market_id": m.market_id,
                "name": m.name,
                "rules": m.rules,
                "close_timestamp": m.close_timestamp
            })
            market_ids.append(m.market_id)

        # Chunk market_ids to avoid URI too large error
        existing_ids = set()
        total_chunks = math.ceil(len(market_ids) / chunk_size)

        for i in range(total_chunks):
            chunk = market_ids[i * chunk_size:(i + 1) * chunk_size]
            response = (
                self.supabase.table("markets")
                .select("market_id")
                .in_("market_id", chunk)
                .execute()
            )
            if response.data:
                existing_ids.update(row["market_id"] for row in response.data)

        # Filter out already existing markets
        new_markets = [m for m in sql_markets if m["market_id"] not in existing_ids]

        if not new_markets:
            print("All markets already exist in the database.")
            return

        # Insert only new markets (chunk again if needed for safety)
        for i in range(0, len(new_markets), chunk_size):
            self.supabase.table("markets").insert(new_markets[i:i + chunk_size]).execute()

    def get_markets(self, market_ids: list[str], chunk_size: int = 100) -> list[Market]:
        """
        Returns a list of Market objects for the given market IDs, chunked to avoid URI limits.
        """
        if not market_ids:
            return []

        markets = []

        for i in range(0, len(market_ids), chunk_size):
            chunk = market_ids[i:i + chunk_size]

            response = (
                self.supabase.table("markets")
                .select("*")
                .in_("market_id", chunk)
                .execute()
            )

            if response.data:
                for row in response.data:
                    market = Market(
                        platform=PlatformType(row["platform"]),
                        market_id=row["market_id"],
                        name=row["name"],
                        rules=row["rules"],
                        close_timestamp=row["close_timestamp"]
                    )
                    markets.append(market)

        return markets


    def add_orderbooks(self, orderbooks: list[Orderbook]) -> None:
        # Convert Orderbook objects to dictionaries
        sql_orderbooks = []
        for ob in orderbooks:
            sql_orderbooks.append({
                "market_id": ob.market_id,
                "timestamp": ob.timestamp,
                "yes_bid": ob.yes["bid"],
                "yes_ask": ob.yes["ask"],
                "no_bid": ob.no["bid"],
                "no_ask": ob.no["ask"]
            })

        # Insert orderbooks into the database
        self.supabase.table("orderbooks").insert(sql_orderbooks).execute()
    
    def new_markets(self, market_ids: list[str]) -> list[str]:
        """
        Returns a list of market IDs that are not already in the database.
        Automatically chunks queries to avoid URL length limits.
        """
        if not market_ids:
            return []

        def chunk_list(lst, size):
            for i in range(0, len(lst), size):
                yield lst[i:i + size]

        existing_ids = set()
        for chunk in chunk_list(market_ids, 50):
            response = (
                self.supabase.table("markets")
                .select("market_id")
                .in_("market_id", chunk)
                .execute()
            )
            if response.data:
                existing_ids.update(row["market_id"] for row in response.data)

        return [m_id for m_id in market_ids if m_id not in existing_ids]

    def add_order(self, order: Order) -> str:
        """
        Adds a new order to the database and returns the generated internal ID.
        """
        order_dict = {
            "market_id": order.market_id,
            "platform": order.platform.value,
            "side": order.side,
            "action": order.action,
            "order_type": order.order_type,
            "quantity": order.size,
            "limit_price": order.price,
            "status": order.status.value,
            "client_order_id": order.client_order_id
        }
        response = self.supabase.table("orders").insert(order_dict).execute()
        
        if response.data:
            return response.data[0]['id']
        raise Exception("Failed to add order to database.")

    def update_order(self, order: Order) -> None:
        """
        Updates an existing order in the database.
        """
        updates = {
            "status": order.status.value,
            "platform_order_id": order.order_id,
            "fill_size": order.fill_size
        }
        self.supabase.table("orders").update(updates).eq("id", order.id).execute()

    def get_unsettled_orders(self) -> list[Order]:
        """
        Fetches all orders that are not in a terminal state (EXECUTED, CANCELED, FAILED).
        """
        response = (
            self.supabase.table("orders")
            .select("*")
            .in_("status", [OrderStatus.PENDING.value, OrderStatus.OPEN.value, OrderStatus.PARTIALLY_FILLED.value])
            .execute()
        )
        
        orders = []
        if response.data:
            for row in response.data:
                order = Order(
                    id=row["id"],
                    market_id=row["market_id"],
                    platform=PlatformType(row["platform"]),
                    side=row["side"],
                    action=row["action"],
                    order_type=row["order_type"],
                    size=row["quantity"],
                    price=row["limit_price"],
                    status=OrderStatus(row["status"]),
                    order_id=row["platform_order_id"],
                    fill_size=row["fill_size"],
                    client_order_id=row["client_order_id"]
                )
                orders.append(order)
        return orders

    def add_trades(self, trades: list[Trade]) -> None:
        """
        Adds new trades to the database.
        """
        trade_dicts = [
            {
                "order_id": trade.order_id,
                "platform_trade_id": trade.platform_trade_id,
                "quantity": trade.quantity,
                "price": trade.price,
                "executed_at": trade.executed_at
            }
            for trade in trades
        ]
        self.supabase.table("trades").insert(trade_dicts).execute()