import time
import os
import signal
from db.DBManager import DBManager
from models.PlatformType import PlatformType
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform

class TradeReconciliationService:
    def __init__(self):
        self.db_manager = DBManager()
        self.platforms = {
            PlatformType.KALSHI: KalshiPlatform(),
            PlatformType.POLYMARKET: PolyMarketPlatform(),
        }
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def reconcile_orders(self):
        """
        Fetches unsettled orders and reconciles their status with the platforms.
        """
        print("Starting order reconciliation cycle...")
        unsettled_orders = self.db_manager.get_unsettled_orders()

        if not unsettled_orders:
            print("No unsettled orders to reconcile.")
            return

        print(f"Found {len(unsettled_orders)} unsettled orders to reconcile.")
        for order in unsettled_orders:
            platform_client = self.platforms.get(order.platform)
            if not platform_client:
                print(f"No platform client found for order {order.id} on platform {order.platform}. Skipping.")
                continue
            
            print(f"Reconciling order {order.id} (Platform ID: {order.order_id}) on {order.platform.value}...")
            new_trades = platform_client.get_order_status(order)
            
            # Persist updates to the database
            self.db_manager.update_order(order)
            if new_trades:
                # A more robust solution would filter out trades that have already been persisted.
                self.db_manager.add_trades(new_trades)
            
            print(f"Finished reconciling order {order.id}. New status: {order.status.value}")

    def run(self):
        """
        Runs the reconciliation service indefinitely.
        """
        polling_interval = int(os.getenv("RECONCILIATION_POLLING_INTERVAL_S", 60))
        print(f"Starting Trade Reconciliation Service with a {polling_interval} second interval...")
        while not self.shutdown_requested:
            self.reconcile_orders()
            if not self.shutdown_requested:
                time.sleep(polling_interval)
        print("Trade Reconciliation Service shut down gracefully.")

if __name__ == '__main__':
    reconciliation_service = TradeReconciliationService()
    reconciliation_service.run() 