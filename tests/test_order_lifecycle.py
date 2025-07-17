import time
import logging
from models.Order import Order
from platform.KalshiPlatform import KalshiPlatform
from platform.PolyMarketPlatform import PolyMarketPlatform
from platform.BasePlatform import BasePlatform
from models.OrderStatus import OrderStatus

# --- CONFIGURATION ---
# Please replace these with active market IDs from the respective platforms
KALSHI_MARKET_ID = None #"ROBOTAXIOUT-26-JAN01"
POLYMARKET_MARKET_ID = "0x310c3d08f015157ec78e04f3f4fefed659b5e2bd88ae80cb38ff27ef970c39bd"

# --- SETUP ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def run_order_lifecycle_test(platform: BasePlatform, market_id: str):
    """
    Runs a comprehensive suite of order lifecycle tests for a given platform.
    
    Tests include:
    1. Market Buy Order
    2. Limit Buy Order (that is likely to fill)
    3. Limit Buy Order (that is unlikely to fill and will be canceled)
    """
    logging.info(f"--- Starting Lifecycle Test for {platform.__class__.__name__} on market {market_id} ---")

    # PolyMarket has a minimum order size of 5
    order_size = 5 if isinstance(platform, PolyMarketPlatform) else 1
    logging.info(f"Using order size: {order_size}")

    # === Test 1: Market Buy Order ===
    logging.info("\n--- Test 1: Market Buy Order ---")
    try:
        market_buy_order = Order.create_market_buy_order(
            market_id=market_id,
            side="yes",
            size=order_size,
            max_price=50  # Max price of 50 cents per contract
        )
        test_placement_and_status_tracking(platform, market_buy_order)
    except Exception as e:
        logging.error(f"Market Buy Order test failed with an exception: {e}", exc_info=True)


    # === Test 2: Limit Buy Order (Likely to Fill) ===
    logging.info("\n--- Test 2: Limit Buy Order (Likely to Fill) ---")
    try:
        limit_buy_fill = Order.create_limit_buy_order(
            market_id=market_id,
            side="yes",
            size=order_size,
            price=10  # Aggressive price, likely to fill
        )
        test_placement_and_status_tracking(platform, limit_buy_fill)
    except Exception as e:
        logging.error(f"Limit Buy (Fill) test failed with an exception: {e}", exc_info=True)


    # === Test 3: Limit Buy Order (Cancel) ===
    logging.info("\n--- Test 3: Limit Buy Order (Cancel) ---")
    try:
        limit_buy_cancel = Order.create_limit_buy_order(
            market_id=market_id,
            side="yes",
            size=order_size,
            price=1  # Unlikely to fill, will be canceled
        )
        test_cancellation(platform, limit_buy_cancel)
    except Exception as e:
        logging.error(f"Limit Buy (Cancel) test failed with an exception: {e}", exc_info=True)
    
    logging.info(f"\n--- Completed Lifecycle Test for {platform.__class__.__name__} ---")


def test_placement_and_status_tracking(platform: BasePlatform, order: Order):
    """Places an order and tracks its status for a few cycles."""
    logging.info(f"Placing {order.order_type} order: size={order.size}, side={order.side}, price={order.price or 'N/A'}")
    platform.place_order(order)

    if order.status == OrderStatus.FAILED:
        logging.error("Order placement failed immediately. Aborting test for this order.")
        return

    assert order.order_id is not None, "Order ID was not set after placement."
    logging.info(f"Order placed successfully. Platform Order ID: {order.order_id}")

    # Track status over time
    for i in range(3):
        logging.info(f"Checking status... (Cycle {i+1}/3)")
        time.sleep(5) # Wait for platform processing
        platform.get_order_status(order)
        logging.info(f"  -> Current Status: {order.status.value}, Fill Size: {order.fill_size}")
        if order.status in [OrderStatus.EXECUTED, OrderStatus.CANCELED, OrderStatus.FAILED]:
            logging.info("Order has reached a terminal state.")
            break

def test_cancellation(platform: BasePlatform, order: Order):
    """Places an order, waits, and then cancels it."""
    logging.info(f"Placing order to be canceled: size={order.size}, side={order.side}, price={order.price}")
    platform.place_order(order)

    if order.status == OrderStatus.FAILED:
        logging.error("Order placement failed immediately. Aborting cancellation test.")
        return
        
    assert order.order_id is not None, "Order ID was not set after placement."
    logging.info(f"Order placed successfully. Platform Order ID: {order.order_id}")

    logging.info("Waiting 5 seconds before cancellation...")
    time.sleep(5)

    logging.info(f"Attempting to cancel order {order.order_id}...")
    platform.cancel_order(order)
    
    # Verify cancellation status
    time.sleep(2)
    platform.get_order_status(order)
    logging.info(f"Final status after cancellation attempt: {order.status.value}")
    assert order.status == OrderStatus.CANCELED, f"Order status was not CANCELED. Was {order.status.value}."
    logging.info("Cancellation successful and status verified.")


if __name__ == "__main__":
    # --- Kalshi Test ---
    if KALSHI_MARKET_ID:
        kalshi_platform = KalshiPlatform()
        run_order_lifecycle_test(kalshi_platform, KALSHI_MARKET_ID)
    else:
        logging.warning("KALSHI_MARKET_ID is not set or is invalid. Skipping Kalshi tests.")

    # --- PolyMarket Test ---
    if POLYMARKET_MARKET_ID and "0x" in POLYMARKET_MARKET_ID:
        polymarket_platform = PolyMarketPlatform()
        run_order_lifecycle_test(polymarket_platform, POLYMARKET_MARKET_ID)
    else:
        logging.warning("POLYMARKET_MARKET_ID is not set or is invalid. Skipping PolyMarket tests.") 