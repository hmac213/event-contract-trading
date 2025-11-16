#!/usr/bin/env python3
"""
Test script for the Mock Trading System
Validates core functionality without requiring Redis or live data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.mock_trade_executor.mock_db_manager import MockDBManager
from models.PlatformType import PlatformType
from models.Order import Order
from models.OrderStatus import OrderStatus
from models.Trade import Trade
import time

def test_mock_db_manager():
    """Test the MockDBManager functionality."""
    print("🧪 Testing Mock Database Manager...")
    
    try:
        mock_db = MockDBManager()
        
        # Test balance initialization
        print("  ✓ Initializing mock balances...")
        mock_db.initialize_mock_balances()
        
        # Test balance retrieval
        kalshi_balance = mock_db.get_mock_balance(PlatformType.KALSHI)
        poly_balance = mock_db.get_mock_balance(PlatformType.POLYMARKET)
        
        print(f"  ✓ Kalshi balance: ${kalshi_balance/100:.2f}")
        print(f"  ✓ PolyMarket balance: ${poly_balance/100:.2f}")
        
        # Test balance update
        print("  ✓ Testing balance updates...")
        mock_db.update_mock_balance(PlatformType.KALSHI, -10000)  # Spend $100
        new_balance = mock_db.get_mock_balance(PlatformType.KALSHI)
        print(f"  ✓ Kalshi balance after $100 spend: ${new_balance/100:.2f}")
        
        # Test order creation
        print("  ✓ Testing mock order creation...")
        test_order = Order.create_market_buy_order(
            market_id="test_market_123",
            platform=PlatformType.KALSHI,
            side="yes",
            size=10,
            max_price=50
        )
        
        order_id = mock_db.add_mock_order(test_order)
        print(f"  ✓ Created mock order with ID: {order_id}")
        
        # Test order update
        test_order.id = order_id
        test_order.status = OrderStatus.EXECUTED
        test_order.order_id = "mock_kalshi_12345"
        test_order.fill_size = 10
        mock_db.update_mock_order(test_order)
        print("  ✓ Updated mock order status")
        
        # Test trade creation
        print("  ✓ Testing mock trade creation...")
        test_trade = Trade(
            order_id=order_id,
            platform_trade_id="mock_trade_67890",
            quantity=10,
            price=48,  # Executed at $0.48 per share
            executed_at=int(time.time())
        )
        
        mock_db.add_mock_trades([test_trade])
        print("  ✓ Created mock trade")
        
        # Test statistics
        print("  ✓ Testing statistics retrieval...")
        stats = mock_db.get_mock_trading_stats()
        print(f"  ✓ Retrieved stats: {len(stats)} categories")
        
        print("🎉 All MockDBManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MockDBManager test failed: {e}")
        return False

def test_order_creation():
    """Test order creation and validation."""
    print("\n🧪 Testing Order Creation...")
    
    try:
        # Test market buy order
        market_order = Order.create_market_buy_order(
            market_id="test_market_456",
            platform=PlatformType.POLYMARKET,
            side="no",
            size=25,
            max_price=75
        )
        
        assert market_order.order_type == "market"
        assert market_order.action == "buy"
        assert market_order.size == 25
        assert market_order.max_price == 75
        print("  ✓ Market buy order created successfully")
        
        # Test limit buy order
        limit_order = Order.create_limit_buy_order(
            market_id="test_market_789",
            platform=PlatformType.KALSHI,
            side="yes",
            size=50,
            price=60
        )
        
        assert limit_order.order_type == "limit"
        assert limit_order.action == "buy"
        assert limit_order.size == 50
        assert limit_order.price == 60
        print("  ✓ Limit buy order created successfully")
        
        print("🎉 All Order creation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Order creation test failed: {e}")
        return False

def test_mock_trading_flow():
    """Test a complete mock trading flow."""
    print("\n🧪 Testing Complete Mock Trading Flow...")
    
    try:
        mock_db = MockDBManager()
        
        # Simulate an arbitrage opportunity
        opportunity = {
            "shares": 20,
            "max_price_1": 450,  # $4.50 in API units
            "max_price_2": 520,  # $5.20 in API units
            "type": "yes1_no2"
        }
        
        # Create orders for the opportunity
        order1 = Order.create_market_buy_order(
            market_id="arb_market_1",
            platform=PlatformType.KALSHI,
            side="yes",
            size=opportunity["shares"],
            max_price=round(opportunity["max_price_1"] / 10)
        )
        
        order2 = Order.create_market_buy_order(
            market_id="arb_market_2",
            platform=PlatformType.POLYMARKET,
            side="no",
            size=opportunity["shares"],
            max_price=round(opportunity["max_price_2"] / 10)
        )
        
        # Add orders to database
        order1.id = mock_db.add_mock_order(order1)
        order2.id = mock_db.add_mock_order(order2)
        
        print(f"  ✓ Created arbitrage orders: {order1.id}, {order2.id}")
        
        # Simulate execution
        for order in [order1, order2]:
            order.status = OrderStatus.EXECUTED
            order.order_id = f"mock_{order.platform.value}_{int(time.time())}"
            order.fill_size = order.size
            mock_db.update_mock_order(order)
            
            # Create corresponding trade
            trade = Trade(
                order_id=order.id,
                platform_trade_id=f"mock_trade_{int(time.time())}",
                quantity=order.size,
                price=order.max_price - 2,  # Simulate 2 cent slippage
                executed_at=int(time.time())
            )
            mock_db.add_mock_trades([trade])
        
        print("  ✓ Simulated order execution and trades")
        
        # Check final statistics
        stats = mock_db.get_mock_trading_stats()
        print(f"  ✓ Final stats - Total trades: {stats['total_trades']}")
        
        print("🎉 Complete mock trading flow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Mock trading flow test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Mock Trading System Tests")
    print("=" * 50)
    
    tests = [
        test_order_creation,
        test_mock_db_manager,
        test_mock_trading_flow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Mock trading system is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
