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




def main():
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




if __name__ == "__main__":
    main()