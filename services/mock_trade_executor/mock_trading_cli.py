#!/usr/bin/env python3
"""
Mock Trading CLI - Utility for managing mock trading operations
"""

import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.mock_trade_executor.mock_db_manager import MockDBManager
from models.PlatformType import PlatformType

def print_balances(mock_db: MockDBManager):
    """Print current mock balances."""
    print("\n💰 Current Mock Balances:")
    print("=" * 40)
    
    for platform in [PlatformType.KALSHI, PlatformType.POLYMARKET]:
        balance = mock_db.get_mock_balance(platform)
        print(f"{platform.value:12}: ${balance/100:>10,.2f}")
    
    print("=" * 40)

def print_stats(mock_db: MockDBManager):
    """Print comprehensive mock trading statistics."""
    stats = mock_db.get_mock_trading_stats()
    
    print("\n📊 Mock Trading Statistics:")
    print("=" * 50)
    
    # Balances
    print("\n💰 Current Balances:")
    for platform, balance in stats["balances"].items():
        initial = stats["starting_balance_per_platform"]
        pnl = balance - initial
        pnl_pct = (pnl / initial) * 100 if initial > 0 else 0
        
        print(f"  {platform:12}: ${balance/100:>10,.2f} (P&L: ${pnl/100:>8,.2f} / {pnl_pct:>6.2f}%)")
    
    # Order statistics
    print(f"\n📋 Order Statistics:")
    if stats["order_stats"]:
        for status, count in stats["order_stats"].items():
            print(f"  {status:15}: {count:>5}")
    else:
        print("  No orders yet")
    
    print(f"\n📈 Trade Summary:")
    print(f"  Total Trades    : {stats['total_trades']:>5}")
    
    # Calculate total P&L
    total_initial = stats["starting_balance_per_platform"] * len(stats["balances"])
    total_current = sum(stats["balances"].values())
    total_pnl = total_current - total_initial
    total_pnl_pct = (total_pnl / total_initial) * 100 if total_initial > 0 else 0
    
    print(f"\n🎯 Overall Performance:")
    print(f"  Total P&L       : ${total_pnl/100:>8,.2f} ({total_pnl_pct:>6.2f}%)")
    print(f"  Starting Capital: ${total_initial/100:>8,.2f}")
    print(f"  Current Capital : ${total_current/100:>8,.2f}")
    
    print("=" * 50)

def reset_data(mock_db: MockDBManager):
    """Reset all mock trading data."""
    print("⚠️  WARNING: This will delete ALL mock trading history!")
    response = input("Are you sure? Type 'yes' to confirm: ")
    
    if response.lower() == 'yes':
        mock_db.reset_mock_data()
        print("✅ Mock trading data has been reset.")
    else:
        print("❌ Reset cancelled.")

def initialize_balances(mock_db: MockDBManager):
    """Initialize mock balances."""
    print("🏦 Initializing mock balances...")
    mock_db.initialize_mock_balances()
    print("✅ Mock balances initialized.")

def main():
    parser = argparse.ArgumentParser(description="Mock Trading CLI")
    parser.add_argument("command", choices=["balances", "stats", "reset", "init"], 
                       help="Command to execute")
    
    args = parser.parse_args()
    
    try:
        mock_db = MockDBManager()
        
        if args.command == "balances":
            print_balances(mock_db)
        elif args.command == "stats":
            print_stats(mock_db)
        elif args.command == "reset":
            reset_data(mock_db)
        elif args.command == "init":
            initialize_balances(mock_db)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
