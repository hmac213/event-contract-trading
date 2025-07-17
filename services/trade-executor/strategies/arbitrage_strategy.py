import time
import os
from models.Market import Market
from models.Order import Order
from models.OrderStatus import OrderStatus
from platform.BasePlatform import BasePlatform

POLLING_TIMEOUT_S = 30  # Max time to wait for a chunk to fill

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
    print(
        f"Starting arbitrage execution for {total_shares} shares between "
        f"{market1.platform.value}/{market1.market_id} and "
        f"{market2.platform.value}/{market2.market_id}."
    )

    max_price_1 = round(opportunity["max_price_1"] / 10)
    max_price_1 = max(1, min(max_price_1, 99))
    
    max_price_2 = round(opportunity["max_price_2"] / 10)
    max_price_2 = max(1, min(max_price_2, 99))

    order_chunk_size = max(1, total_shares // 10)

    while shares_executed < total_shares:
        chunk_size = min(order_chunk_size, total_shares - shares_executed)
        print(f"Executing chunk: {chunk_size} shares ({shares_executed}/{total_shares} completed).")

        if opportunity["type"] == "yes1_no2":
            side1, side2 = "yes", "no"
        elif opportunity["type"] == "yes2_no1":
            side1, side2 = "no", "yes"
        else:
            print(f"Invalid opportunity type: {opportunity['type']}. Aborting.")
            return

        order1 = Order.create_market_buy_order(market1.market_id, side1, chunk_size, max_price_1)
        order2 = Order.create_market_buy_order(market2.market_id, side2, chunk_size, max_price_2)

        platform1.place_order(order1)
        platform2.place_order(order2)

        if order1.status == OrderStatus.FAILED or order2.status == OrderStatus.FAILED:
            print("One or both orders failed immediately on placement. Aborting arbitrage.")
            if order1.status != OrderStatus.FAILED and order1.order_id:
                platform1.cancel_order(order1)
            if order2.status != OrderStatus.FAILED and order2.order_id:
                platform2.cancel_order(order2)
            return

        print(f"Chunk orders placed. O1: {order1.order_id}, O2: {order2.order_id}. Awaiting execution...")

        if not _wait_for_execution(platform1, order1, platform2, order2):
            print("Failed to confirm chunk execution. Halting arbitrage.")
            return

        shares_executed += chunk_size

    print(f"Successfully executed all {total_shares} shares for the arbitrage opportunity.")

def _wait_for_execution(p1: BasePlatform, o1: Order, p2: BasePlatform, o2: Order) -> bool:
    """Polls two orders until they are both executed or a timeout is reached."""
    polling_timeout = int(os.getenv("POLLING_TIMEOUT_S", 30))
    start_time = time.time()
    o1_filled = False
    o2_filled = False

    while time.time() - start_time < polling_timeout:
        if not o1_filled:
            p1.get_order_status(o1)
            if o1.status == OrderStatus.EXECUTED:
                o1_filled = True
                print(f"Order 1 ({o1.order_id}) confirmed EXECUTED.")
        
        if not o2_filled:
            p2.get_order_status(o2)
            if o2.status == OrderStatus.EXECUTED:
                o2_filled = True
                print(f"Order 2 ({o2.order_id}) confirmed EXECUTED.")

        if o1_filled and o2_filled:
            return True
        
        if o1.status in [OrderStatus.CANCELED, OrderStatus.FAILED] or \
           o2.status in [OrderStatus.CANCELED, OrderStatus.FAILED]:
            print(f"Order failed during execution poll. O1:{o1.status.value}, O2:{o2.status.value}.")
            if o1.status == OrderStatus.OPEN: p1.cancel_order(o1)
            if o2.status == OrderStatus.OPEN: p2.cancel_order(o2)
            return False

    print(f"Polling timed out after {polling_timeout}s. O1:{o1.status.value}, O2:{o2.status.value}.")
    if o1.status == OrderStatus.OPEN: p1.cancel_order(o1)
    if o2.status == OrderStatus.OPEN: p2.cancel_order(o2)
    return False 