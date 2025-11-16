from models.PlatformType import PlatformType
from models.Order import Order
from models.Trade import Trade
from models.OrderStatus import OrderStatus
from supabase import create_client
import os
import logging
from postgrest.exceptions import APIError

class MockDBManager:
    """
    Manages mock balances, orders, and trades for testing purposes.
    Uses separate database tables to avoid interfering with real trading data.
    """
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Starting balance in cents ($50,000 = 5,000,000 cents)
        self.STARTING_BALANCE = 5_000_000

    def initialize_mock_balances(self):
        """
        Initialize mock balances for both platforms with $50,000 each.
        Only creates if they don't already exist.
        """
        try:
            # Check if balances already exist
            response = self.supabase.table("mock_balances").select("*").execute()
            
            existing_platforms = set()
            if response.data:
                existing_platforms = {row["platform"] for row in response.data}
            
            balances_to_create = []
            for platform in [PlatformType.KALSHI, PlatformType.POLYMARKET]:
                if platform.value not in existing_platforms:
                    balances_to_create.append({
                        "platform": platform.value,
                        "balance": self.STARTING_BALANCE,
                        "initial_balance": self.STARTING_BALANCE
                    })
            
            if balances_to_create:
                self.supabase.table("mock_balances").insert(balances_to_create).execute()
                print(f"🏦 Initialized mock balances for {len(balances_to_create)} platforms")
            else:
                print("🏦 Mock balances already initialized")
                
        except Exception as e:
            print(f"⚠️ Error initializing mock balances: {e}")
            # If table doesn't exist, we'll create it on first use
            pass

    def get_mock_balance(self, platform: PlatformType) -> int:
        """
        Get the current mock balance for a platform in cents.
        """
        try:
            response = (
                self.supabase.table("mock_balances")
                .select("balance")
                .eq("platform", platform.value)
                .execute()
            )
            
            if response.data:
                return response.data[0]["balance"]
            else:
                # Initialize if doesn't exist
                self._create_mock_balance(platform)
                return self.STARTING_BALANCE
                
        except Exception as e:
            print(f"⚠️ Error getting mock balance for {platform.value}: {e}")
            return self.STARTING_BALANCE

    def _create_mock_balance(self, platform: PlatformType):
        """Create a mock balance entry for a platform."""
        try:
            self.supabase.table("mock_balances").insert({
                "platform": platform.value,
                "balance": self.STARTING_BALANCE,
                "initial_balance": self.STARTING_BALANCE
            }).execute()
        except Exception as e:
            print(f"⚠️ Error creating mock balance for {platform.value}: {e}")

    def update_mock_balance(self, platform: PlatformType, amount_change: int):
        """
        Update mock balance by adding/subtracting an amount (in cents).
        Positive amount = credit, Negative amount = debit
        """
        try:
            current_balance = self.get_mock_balance(platform)
            new_balance = current_balance + amount_change
            
            self.supabase.table("mock_balances").update({
                "balance": new_balance
            }).eq("platform", platform.value).execute()
            
            print(f"💰 Updated {platform.value} balance: ${current_balance/100:.2f} -> ${new_balance/100:.2f}")
            
        except Exception as e:
            print(f"⚠️ Error updating mock balance for {platform.value}: {e}")

    def add_mock_order(self, order: Order) -> str:
        """
        Adds a new mock order to the database and returns the generated internal ID.
        """
        try:
            order_dict = {
                "market_id": order.market_id,
                "platform": order.platform.value,
                "side": order.side,
                "action": order.action,
                "order_type": order.order_type,
                "quantity": order.size,
                "limit_price": order.price,
                "status": order.status.value,
                "client_order_id": order.client_order_id,
                "platform_order_id": order.order_id,
                "fill_size": order.fill_size
            }
            response = self.supabase.table("mock_orders").insert(order_dict).execute()
            
            if response.data:
                return response.data[0]['id']
            raise Exception("Failed to add mock order to database.")
            
        except Exception as e:
            print(f"⚠️ Error adding mock order: {e}")
            raise

    def update_mock_order(self, order: Order) -> None:
        """
        Updates an existing mock order in the database.
        """
        try:
            updates = {
                "status": order.status.value,
                "platform_order_id": order.order_id,
                "fill_size": order.fill_size
            }
            self.supabase.table("mock_orders").update(updates).eq("id", order.id).execute()
            
        except Exception as e:
            print(f"⚠️ Error updating mock order: {e}")

    def add_mock_trades(self, trades: list[Trade]) -> None:
        """
        Adds new mock trades to the database.
        """
        try:
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
            self.supabase.table("mock_trades").insert(trade_dicts).execute()
            print(f"📝 Added {len(trades)} mock trades to database")
            
        except Exception as e:
            print(f"⚠️ Error adding mock trades: {e}")

    def get_mock_trading_stats(self) -> dict:
        """
        Get comprehensive mock trading statistics.
        """
        try:
            # Get current balances
            balances = {}
            for platform in [PlatformType.KALSHI, PlatformType.POLYMARKET]:
                balances[platform.value] = self.get_mock_balance(platform)
            
            # Get order counts by status
            order_response = self.supabase.table("mock_orders").select("status").execute()
            order_stats = {}
            if order_response.data:
                for row in order_response.data:
                    status = row["status"]
                    order_stats[status] = order_stats.get(status, 0) + 1
            
            # Get trade count
            trade_response = self.supabase.table("mock_trades").select("id").execute()
            trade_count = len(trade_response.data) if trade_response.data else 0
            
            return {
                "balances": balances,
                "order_stats": order_stats,
                "total_trades": trade_count,
                "starting_balance_per_platform": self.STARTING_BALANCE
            }
            
        except Exception as e:
            print(f"⚠️ Error getting mock trading stats: {e}")
            return {"error": str(e)}

    def reset_mock_data(self):
        """
        Reset all mock data back to initial state.
        WARNING: This deletes all mock trading history!
        """
        try:
            # Reset balances
            self.supabase.table("mock_balances").update({
                "balance": self.STARTING_BALANCE
            }).neq("platform", "").execute()
            
            # Delete all mock orders and trades
            self.supabase.table("mock_orders").delete().neq("id", "").execute()
            self.supabase.table("mock_trades").delete().neq("id", "").execute()
            
            print("🔄 Reset all mock trading data to initial state")
            
        except Exception as e:
            print(f"⚠️ Error resetting mock data: {e}")

    def get_unsettled_mock_orders(self) -> list[Order]:
        """
        Fetches all mock orders that are not in a terminal state.
        """
        try:
            response = (
                self.supabase.table("mock_orders")
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
            
        except Exception as e:
            print(f"⚠️ Error getting unsettled mock orders: {e}")
            return []
