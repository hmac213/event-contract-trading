from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from supabase import create_client
import os

class DBManager():
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

    def add_markets(self, markets: list[Market]) -> None:
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

        # Query existing market_ids
        existing_response = (
            self.supabase.table("markets")
            .select("market_id")
            .in_("market_id", market_ids)
            .execute()
        )

        existing_ids = set(row["market_id"] for row in existing_response.data)

        # Filter out already existing markets
        new_markets = [m for m in sql_markets if m["market_id"] not in existing_ids]

        if not new_markets:
            print("All markets already exist in the database.")
            return

        # Insert only new markets
        self.supabase.table("markets").insert(new_markets).execute()
        
        
            

    def add_book_order(self, orderbook: Orderbook) -> None:
        pass

    def get_order_books(self, market_ids: list[str]) -> list[Orderbook]:

        pass