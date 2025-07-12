#!/usr/bin/env python3
"""
Test script to demonstrate the functionality of PolyMarketPlatform class.
This script shows the complete workflow:
1. Finding new markets from PolyMarket
2. Getting market details
3. Getting order books for the markets
"""

from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from datetime import datetime

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

def main():
    """Main test function"""
    print("PolyMarketPlatform Demonstration")
    print("This script demonstrates the complete workflow of the PolyMarketPlatform class")
    
    # Initialize the PolyMarket platform
    platform = KalshiPlatform()
    
    # Step 1: Find new markets
    print_separator("STEP 1: Finding New Markets from PolyMarket")
    num_markets = 3
    print(f"Requesting {num_markets} new markets from PolyMarket API...")
    
    market_ids = platform.find_new_markets(num_markets)
    print(f"Found {len(market_ids)} market IDs:")
    for i, market_id in enumerate(market_ids, 1):
        print(f"  {i}. {market_id}")
    
    if not market_ids:
        print("No markets found. This could be due to:")
        print("  - Network connectivity issues")
        print("  - PolyMarket API changes")
        print("  - Rate limiting")
        print("\nTrying with fallback test data...")
        
        # Use some example market IDs for testing
        market_ids = [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x567890abcdef1234567890abcdef1234567890ab"
        ]
        print(f"Using test market IDs: {market_ids}")
    
    # Step 2: Get market details
    print_separator("STEP 2: Getting Market Details")
    print(f"Fetching details for {len(market_ids)} markets...")
    
    markets = platform.get_markets(market_ids)
    print(f"Retrieved {len(markets)} market objects:")
    
    for i, market in enumerate(markets, 1):
        print(f"\n  Market {i}:")
        print(f"    Platform: {market.platform.value}")
        print(f"    ID: {market.market_id[:20]}...") # Truncate long IDs
        print(f"    Name: {market.name}")
        print(f"    Rules: {market.rules[:100]}...") # Truncate long rules
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
    print(f"PolyMarketPlatform demonstration completed:")
    print(f"  • Found {len(market_ids)} market IDs")
    print(f"  • Retrieved {len(markets)} market details")
    print(f"  • Fetched {len(orderbooks)} order books")
    print(f"  • Platform: {markets[0].platform.value if markets else 'N/A'}")
    
    # Test edge cases
    print_separator("EDGE CASE TESTING")
    
    # Test with 0 markets
    print("Testing with 0 markets:")
    empty_markets = platform.find_new_markets(0)
    print(f"  Result: {len(empty_markets)} markets (expected: 0)")
    
    # Test with empty market list
    print("\nTesting with empty market ID list:")
    empty_orderbooks = platform.get_order_books([])
    print(f"  Result: {len(empty_orderbooks)} order books (expected: 0)")
    
    print("\n" + "="*60)
    print(" PolyMarket Platform test completed! ")
    print("="*60)

if __name__ == "__main__":
    main()
