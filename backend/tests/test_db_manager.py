#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.db.DBManager import DBManager
from backend.models.Market import Market
from backend.models.PlatformType import PlatformType
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform


def print_separator(title):
    """Print a nice separator with title"""
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)


def test_db_manager():
    """Test the DBManager functionality with real markets from Kalshi and Polymarket"""
    
    print_separator("DBManager Test - Real Market Fetching and Database Insertion")
    
    # Initialize DBManager
    print("1. Initializing DBManager...")
    try:
        db_manager = DBManager()
        print("✅ DBManager initialized successfully")
        
        # Check if environment variables are set
        if not db_manager.supabase_url or not db_manager.supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
            print("💡 Please set these environment variables before running the test:")
            print("   export SUPABASE_URL='your_supabase_url'")
            print("   export SUPABASE_KEY='your_supabase_anon_key'")
            return
            
    except Exception as e:
        print(f"❌ Error initializing DBManager: {e}")
        return
    
    print_separator("Initializing Platform Clients")
    
    platforms = {
        PlatformType.KALSHI: KalshiPlatform(),
        PlatformType.POLYMARKET: PolyMarketPlatform()
    }
    
    # Fetch Kalshi markets
    for _, a_platform in platforms.items():
        market_ids = a_platform.find_new_markets(100)
        if market_ids:
            db_manager.add_markets(a_platform.get_markets(market_ids))

    print_separator("Test Summary")
    print("🎯 Test completed!")

    print("\n💡 Check your Supabase dashboard to verify the real markets were inserted correctly.")



if __name__ == "__main__":
    print("🚀 Starting Real Market DBManager Tests...")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run the main test
    test_db_manager()
    

    print("\n🏁 All real market tests completed!")
