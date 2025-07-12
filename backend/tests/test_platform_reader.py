#!/usr/bin/env python3
"""
Platform Reader Test - Demonstrates the functionality of all platform classes.
This script shows the complete workflow:
1. Finding new markets from each platform
2. Getting market details
3. Getting order books for the markets

Run from the project root directory:
    python -m backend.tests.test_platform_reader
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.platform.TestPlatform import TestPlatform


def print_separator(title):
    """Print a nice separator with title"""
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)


def format_timestamp(timestamp):
    """Convert timestamp to readable format"""
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')


def print_orderbook_data(orderbook):
    """Print orderbook data in a readable format"""
    print(f"Market ID: {orderbook.market_id}")
    print(f"Timestamp: {format_timestamp(orderbook.timestamp)}")
    
    # Print YES contract data
    print("\n  YES Bid Contract:")
    if orderbook.yes and len(orderbook.yes) >= 2:
        yes_bids = orderbook.yes['bid'][0]  # prices
        yes_bid_quantities = orderbook.yes['bid'][1]  # quantities
        print(f"    Bids (All): Prices={yes_bids}, Quantities={yes_bid_quantities}")

    print("\n  YES Ask Contract:")
    if orderbook.yes and len(orderbook.yes) >= 2:
        yes_asks = orderbook.yes['ask'][0]  # prices
        yes_ask_quantities = orderbook.yes['ask'][1]  # quantities
        print(f"    Asks (All): Prices={yes_asks}, Quantities={yes_ask_quantities}")
        
    # Print NO contract data
    print("\n  NO Bid Contract:")
    if orderbook.no and len(orderbook.no) >= 2:
        no_bids = orderbook.no['bid'][0]  # prices
        no_bid_quantities = orderbook.no['bid'][1]  # quantities
        print(f"    Bids (All): Prices={no_bids}, Quantities={no_bid_quantities}")

    print("\n  NO Ask Contract:")
    if orderbook.no and len(orderbook.no) >= 2:
        no_asks = orderbook.no['ask'][0]  # prices
        no_ask_quantities = orderbook.no['ask'][1]  # quantities
        print(f"    Asks (All): Prices={no_asks}, Quantities={no_ask_quantities}")


def test_platform(platform, platform_name: str, num_markets: int = 3):
    """
    Test a specific platform with comprehensive logging.
    
    Args:
        platform: Platform instance to test
        platform_name: Name of the platform for logging
        num_markets: Number of markets to test with
        
    Returns:
        Tuple of (success, markets, orderbooks, error_msg)
    """
    print_separator(f"Testing {platform_name}")
    
    try:
        # Step 1: Find new markets
        print(f"Step 1: Finding {num_markets} new markets from {platform_name}...")
        market_ids = platform.find_new_markets(num_markets)
        
        if not market_ids:
            print(f"⚠️  No market IDs found for {platform_name}")
            return False, [], [], "No market IDs found"
        
        print(f"✅ Found {len(market_ids)} market IDs:")
        for i, market_id in enumerate(market_ids, 1):
            print(f"  {i}. {market_id}")
        
        # Step 2: Get market details
        print(f"\nStep 2: Getting market details...")
        markets = platform.get_markets(market_ids)
        print(f"✅ Retrieved {len(markets)} market objects:")
        
        for i, market in enumerate(markets, 1):
            print(f"\n  Market {i}:")
            print(f"    Platform: {market.platform.value}")
            print(f"    ID: {market.market_id[:20]}...")  # Truncate long IDs
            print(f"    Name: {market.name}")
            print(f"    Rules: {market.rules[:100]}...")  # Truncate long rules
            print(f"    Close Time: {format_timestamp(market.close_timestamp)}")
        
        # Step 3: Get order books (limit to first market to avoid rate limiting)
        print(f"\nStep 3: Getting order books...")
        test_market_ids = market_ids[:1]  # Only test first market
        orderbooks = platform.get_order_books(test_market_ids)
        print(f"✅ Retrieved {len(orderbooks)} order books:")
        
        for i, orderbook in enumerate(orderbooks, 1):
            print(f"\n--- Order Book {i} ---")
            print_orderbook_data(orderbook)
        
        print(f"\n✅ {platform_name} test completed successfully!")
        return True, markets, orderbooks, None
        
    except Exception as e:
        error_msg = f"❌ Error testing {platform_name}: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False, [], [], str(e)


def test_edge_cases(platform, platform_name: str):
    """Test edge cases for a platform."""
    print_separator(f"Edge Case Testing for {platform_name}")
    
    try:
        # Test with 0 markets
        print("Testing with 0 markets:")
        empty_markets = platform.find_new_markets(0)
        print(f"  ✅ Result: {len(empty_markets)} markets (expected: 0)")
        
        # Test with empty market list
        print("\nTesting with empty market ID list:")
        empty_orderbooks = platform.get_order_books([])
        print(f"  ✅ Result: {len(empty_orderbooks)} order books (expected: 0)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Edge case test failed: {e}")
        return False


def test_all_platforms():
    """Test all platforms and provide a comprehensive report."""
    print("🚀 Platform Reader Test Suite Starting")
    print("This script demonstrates the complete workflow of all platform classes")
    
    platforms = [
        (KalshiPlatform(), "KalshiPlatform"),
        (TestPlatform(), "TestPlatform"),
        (PolyMarketPlatform(), "PolyMarketPlatform")
    ]
    
    results = {}
    
    for platform, platform_name in platforms:
        success, markets, orderbooks, error = test_platform(platform, platform_name, 3)
        results[platform_name] = {
            'success': success,
            'markets': len(markets),
            'orderbooks': len(orderbooks),
            'error': error
        }
        
        if success:
            test_edge_cases(platform, platform_name)
    
    # Summary Report
    print_separator("FINAL TEST SUMMARY")
    total_markets = 0
    total_orderbooks = 0
    successful_platforms = 0
    
    for platform_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{platform_name}: {status}")
        print(f"  Markets: {result['markets']}")
        print(f"  Orderbooks: {result['orderbooks']}")
        if result['error']:
            print(f"  Error: {result['error']}")
        print()
        
        if result['success']:
            successful_platforms += 1
            total_markets += result['markets']
            total_orderbooks += result['orderbooks']
    
    print(f"Overall Results:")
    print(f"  Successful Platforms: {successful_platforms}/{len(platforms)}")
    print(f"  Total Markets Retrieved: {total_markets}")
    print(f"  Total Orderbooks Retrieved: {total_orderbooks}")
    
    if successful_platforms == len(platforms):
        print("\n🎉 All platform tests PASSED!")
        return True
    else:
        print(f"\n⚠️  {len(platforms) - successful_platforms} platform test(s) FAILED!")
        return False


def main():
    """Main function - test with original Kalshi focus for compatibility"""
    print("Platform Reader Demonstration")
    print("This script demonstrates the complete workflow of the platform classes")
    
    # Initialize the Kalshi platform (as in original)
    platform = KalshiPlatform()
    
    # Step 1: Find new markets
    print_separator("STEP 1: Finding New Markets from Kalshi")
    num_markets = 3
    print(f"Requesting {num_markets} new markets from Kalshi API...")
    
    market_ids = platform.find_new_markets(num_markets)
    print(f"Found {len(market_ids)} market IDs:")
    for i, market_id in enumerate(market_ids, 1):
        print(f"  {i}. {market_id}")
    
    if not market_ids:
        print("No markets found. This could be due to:")
        print("  - Network connectivity issues")
        print("  - Kalshi API changes")
        print("  - Rate limiting")
        return
    
    # Step 2: Get market details
    print_separator("STEP 2: Getting Market Details")
    print(f"Fetching details for {len(market_ids)} markets...")
    
    markets = platform.get_markets(market_ids)
    print(f"Retrieved {len(markets)} market objects:")
    
    for i, market in enumerate(markets, 1):
        print(f"\n  Market {i}:")
        print(f"    Platform: {market.platform.value}")
        print(f"    ID: {market.market_id[:20]}...")  # Truncate long IDs
        print(f"    Name: {market.name}")
        print(f"    Rules: {market.rules[:100]}...")  # Truncate long rules
        print(f"    Close Time: {format_timestamp(market.close_timestamp)}")
    
    # Step 3: Get order books (limit to first market to avoid rate limiting)
    print_separator("STEP 3: Getting Order Books")
    test_market_ids = market_ids[:1]  # Only test first market
    print(f"Fetching order book for 1 market to avoid rate limiting...")
    
    orderbooks = platform.get_order_books(test_market_ids)
    print(f"Retrieved {len(orderbooks)} order books:")
    
    for i, orderbook in enumerate(orderbooks, 1):
        print(f"\n--- Order Book {i} ---")
        print_orderbook_data(orderbook)
    
    # Summary
    print_separator("SUMMARY")
    print(f"Platform Reader demonstration completed:")
    print(f"  • Found {len(market_ids)} market IDs")
    print(f"  • Retrieved {len(markets)} market details")
    print(f"  • Fetched {len(orderbooks)} order books")
    print(f"  • Platform: {markets[0].platform.value if markets else 'N/A'}")
    
    # Test edge cases
    test_edge_cases(platform, "KalshiPlatform")
    
    print("\n" + "="*60)
    print(" Platform Reader test completed! ")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        test_all_platforms()
    else:
        main()
