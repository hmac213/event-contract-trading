import logging
import time
from backend.models.Market import Market
from backend.models.Order import Order
from backend.models.OrderStatus import OrderStatus
from backend.platform.BasePlatform import BasePlatform

# --- CONFIGURATION ---
POLLING_TIMEOUT_S = 30  # Max time to wait for a chunk to fill

class ExecuteArbitrage:
    @staticmethod
    def place_arbitrage_orders(
        market1: Market,
        market2: Market,
        platform1: BasePlatform,
        platform2: BasePlatform,
        opportunity: dict,
    ) -> None:
        """
        Executes an arbitrage opportunity by breaking it into chunks and ensuring
        each chunk is filled before proceeding to the next.
        """
        total_shares = opportunity["shares"]
        shares_executed = 0
        logging.info(
            f"Starting arbitrage execution for {total_shares} shares between "
            f"{market1.platform.value}/{market1.market_id} and "
            f"{market2.platform.value}/{market2.market_id}."
        )

        # The max_prices from the opportunity are in tenths of a cent.
        # The Order factory expects cents, so we divide by 10.
        max_price_1 = round(opportunity["max_price_1"] / 10)
        max_price_1 = max(1, min(max_price_1, 99)) # Clamp between 1 and 99 cents
        
        max_price_2 = round(opportunity["max_price_2"] / 10)
        max_price_2 = max(1, min(max_price_2, 99)) # Clamp between 1 and 99 cents

        # Chunk size is 1/10th of the total, with a minimum of 1
        order_chunk_size = max(1, total_shares // 10)

        while shares_executed < total_shares:
            chunk_size = min(order_chunk_size, total_shares - shares_executed)
            logging.info(f"Executing chunk: {chunk_size} shares ({shares_executed}/{total_shares} completed).")

            if opportunity["type"] == "yes1_no2":
                side1, side2 = "yes", "no"
            elif opportunity["type"] == "yes2_no1":
                side1, side2 = "no", "yes"
            else:
                logging.error(f"Invalid opportunity type: {opportunity['type']}. Aborting.")
                return

            order1 = Order.create_market_buy_order(market1.market_id, side1, chunk_size, max_price_1)
            order2 = Order.create_market_buy_order(market2.market_id, side2, chunk_size, max_price_2)

            # --- Place Orders ---
            platform1.place_order(order1)
            platform2.place_order(order2)

            if order1.status == OrderStatus.FAILED or order2.status == OrderStatus.FAILED:
                logging.error("One or both orders failed immediately on placement. Aborting arbitrage.")
                # Attempt to cancel the other order if it was successfully placed
                if order1.status != OrderStatus.FAILED and order1.order_id:
                    platform1.cancel_order(order1)
                if order2.status != OrderStatus.FAILED and order2.order_id:
                    platform2.cancel_order(order2)
                return

            logging.info(f"Chunk orders placed. O1: {order1.order_id}, O2: {order2.order_id}. Awaiting execution...")

            # --- Poll for Execution ---
            if not ExecuteArbitrage._wait_for_execution(platform1, order1, platform2, order2):
                logging.error("Failed to confirm chunk execution. Halting arbitrage.")
                return

            shares_executed += chunk_size

        logging.info(f"Successfully executed all {total_shares} shares for the arbitrage opportunity.")

    @staticmethod
    def _wait_for_execution(p1: BasePlatform, o1: Order, p2: BasePlatform, o2: Order) -> bool:
        """Polls two orders until they are both executed or a timeout is reached."""
        start_time = time.time()
        o1_filled = False
        o2_filled = False

        while time.time() - start_time < POLLING_TIMEOUT_S:
            if not o1_filled:
                p1.get_order_status(o1)
                if o1.status == OrderStatus.EXECUTED:
                    o1_filled = True
                    logging.info(f"Order 1 ({o1.order_id}) confirmed EXECUTED.")
            
            if not o2_filled:
                p2.get_order_status(o2)
                if o2.status == OrderStatus.EXECUTED:
                    o2_filled = True
                    logging.info(f"Order 2 ({o2.order_id}) confirmed EXECUTED.")

            if o1_filled and o2_filled:
                return True
            
            # Check for failures during polling
            if o1.status in [OrderStatus.CANCELED, OrderStatus.FAILED] or \
               o2.status in [OrderStatus.CANCELED, OrderStatus.FAILED]:
                logging.error(f"Order failed during execution poll. O1:{o1.status.value}, O2:{o2.status.value}.")
                # Attempt to cancel the other order if it's still open
                if o1.status == OrderStatus.OPEN: p1.cancel_order(o1)
                if o2.status == OrderStatus.OPEN: p2.cancel_order(o2)
                return False

        logging.error(f"Polling timed out after {POLLING_TIMEOUT_S}s. O1:{o1.status.value}, O2:{o2.status.value}.")
        if o1.status == OrderStatus.OPEN: p1.cancel_order(o1)
        if o2.status == OrderStatus.OPEN: p2.cancel_order(o2)
        return False 