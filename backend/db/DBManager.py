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
        """

        if not market_ids:
            return []

        # Query existing market_ids
        response = (
            self.supabase.table("markets")
            .select("market_id")
            .in_("market_id", market_ids)
            .execute()
        )

        existing_ids = set(row["market_id"] for row in response.data)

        # Filter out existing market IDs
        new_market_ids = [m_id for m_id in market_ids if m_id not in existing_ids]

        return new_market_ids