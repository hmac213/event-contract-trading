import time
import os
import uuid
from models.Market import Market
from models.Order import Order
from models.OrderStatus import OrderStatus
from models.Trade import Trade
from platforms.BasePlatform import BasePlatform
from services.mock_trade_executor.mock_db_manager import MockDBManager

def create_mock_arbitrage_orders(
    market1: Market,
    market2: Market,
    platform1: BasePlatform,
    platform2: BasePlatform,
    opportunity: dict,
    mock_db_manager: MockDBManager,
) -> None:
    """
    Executes a MOCK arbitrage opportunity by simulating the trade execution process.
    This mirrors the real arbitrage strategy but uses mock orders and trades.
    """
    total_shares = opportunity["shares"]
    shares_executed = 0
    print(
        f"🎭 Mock Arbitrage: Starting execution for {total_shares} shares between "
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
        print(f"🎭 Mock Arbitrage: Executing chunk: {chunk_size} shares ({shares_executed}/{total_shares} completed).")

        if opportunity["type"] == "yes1_no2":
            side1, side2 = "yes", "no"
        elif opportunity["type"] == "yes2_no1":
            side1, side2 = "no", "yes"
        else:
            print(f"🎭 Mock Arbitrage: Invalid opportunity type: {opportunity['type']}. Aborting.")
            return

        # Create mock orders (same structure as real orders)
        order1 = Order.create_market_buy_order(market1.market_id, market1.platform, side1, chunk_size, max_price_1)
        order2 = Order.create_market_buy_order(market2.market_id, market2.platform, side2, chunk_size, max_price_2)
        
        # Add orders to mock database
        order1.id = mock_db_manager.add_mock_order(order1)
        order2.id = mock_db_manager.add_mock_order(order2)

        # Simulate order placement (no real API calls)
        _simulate_order_placement(order1, platform1, mock_db_manager)
        _simulate_order_placement(order2, platform2, mock_db_manager)

        if order1.status == OrderStatus.FAILED or order2.status == OrderStatus.FAILED:
            print("🎭 Mock Arbitrage: One or both orders failed immediately on placement. Aborting arbitrage.")
            return

        print(f"🎭 Mock Arbitrage: Chunk orders placed. O1: {order1.order_id}, O2: {order2.order_id}. Awaiting execution...")

        if not _simulate_execution_wait(order1, order2, mock_db_manager):
            print("🎭 Mock Arbitrage: Failed to confirm chunk execution. Halting arbitrage.")
            return

        shares_executed += chunk_size

    print(f"🎭 Mock Arbitrage: Successfully executed all {total_shares} shares for the arbitrage opportunity.")

def _simulate_order_placement(order: Order, platform: BasePlatform, mock_db_manager: MockDBManager) -> None:
    """
    Simulates placing an order on a platform.
    """
    # Generate a mock platform order ID
    order.order_id = f"mock_{platform.__class__.__name__.lower()}_{uuid.uuid4().hex[:8]}"
    order.status = OrderStatus.OPEN
    
    # Update the order in mock database
    mock_db_manager.update_mock_order(order)
    
    # Deduct balance for the order (simulate escrow)
    cost = _calculate_order_cost(order)
    mock_db_manager.update_mock_balance(order.platform, -cost)
    
    print(f"🎭 Mock Order: Placed {order.side} order for {order.size} shares at max ${order.max_price or order.price} on {order.platform.value}")

def _calculate_order_cost(order: Order) -> int:
    """
    Calculate the cost of an order in cents.
    """
    price = order.max_price if order.order_type == "market" else order.price
    return order.size * price

def _simulate_execution_wait(order1: Order, order2: Order, mock_db_manager: MockDBManager) -> bool:
    """
    Simulates waiting for order execution with realistic timing.
    """
    execution_delay = float(os.getenv("MOCK_EXECUTION_DELAY_S", 2.0))
    
    print(f"🎭 Mock Execution: Waiting {execution_delay}s for order execution simulation...")
    time.sleep(execution_delay)
    
    # Simulate successful execution (90% success rate)
    import random
    if random.random() < 0.9:
        # Execute both orders
        _simulate_order_execution(order1, mock_db_manager)
        _simulate_order_execution(order2, mock_db_manager)
        
        print(f"🎭 Mock Execution: Both orders executed successfully")
        return True
    else:
        # Simulate partial failure
        print(f"🎭 Mock Execution: Orders failed to execute (simulated market conditions)")
        order1.status = OrderStatus.CANCELED
        order2.status = OrderStatus.CANCELED
        
        # Refund the escrowed amounts
        cost1 = _calculate_order_cost(order1)
        cost2 = _calculate_order_cost(order2)
        mock_db_manager.update_mock_balance(order1.platform, cost1)  # Refund
        mock_db_manager.update_mock_balance(order2.platform, cost2)  # Refund
        
        mock_db_manager.update_mock_order(order1)
        mock_db_manager.update_mock_order(order2)
        
        return False

def _simulate_order_execution(order: Order, mock_db_manager: MockDBManager) -> None:
    """
    Simulates the execution of an order with realistic price slippage.
    """
    # Simulate price slippage (0-3% worse than expected)
    import random
    slippage_factor = 1 + (random.random() * 0.03)  # 0-3% slippage
    
    if order.order_type == "market":
        # For market orders, use a price slightly worse than max_price
        executed_price = min(99, int(order.max_price * slippage_factor))
    else:
        # For limit orders, execute at limit price
        executed_price = order.price
    
    # Mark order as executed
    order.status = OrderStatus.EXECUTED
    order.fill_size = order.size
    mock_db_manager.update_mock_order(order)
    
    # Create mock trade record
    trade = Trade(
        order_id=order.id,
        platform_trade_id=f"mock_trade_{uuid.uuid4().hex[:8]}",
        quantity=order.size,
        price=executed_price,
        executed_at=int(time.time())
    )
    
    mock_db_manager.add_mock_trades([trade])
    
    # Calculate the difference between escrowed amount and actual cost
    escrowed_cost = _calculate_order_cost(order)
    actual_cost = order.size * executed_price
    refund = escrowed_cost - actual_cost
    
    if refund > 0:
        mock_db_manager.update_mock_balance(order.platform, refund)
    
    print(f"🎭 Mock Trade: Executed {order.size} shares at ${executed_price/100:.2f} per share")

def get_mock_execution_summary(mock_db_manager: MockDBManager) -> dict:
    """
    Get a summary of mock trading activity.
    """
    return mock_db_manager.get_mock_trading_stats()
