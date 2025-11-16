#!/usr/bin/env python3
"""
Redis Stream Recovery Utilities
Provides tools to fix broken streams and recover from data schema issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cache.RedisManager import RedisManager
import argparse

class StreamRecovery:
    def __init__(self):
        self.redis_manager = RedisManager()
    
    def clear_stream(self, stream_name: str, confirm: bool = False):
        """Clear a Redis stream completely."""
        if not confirm:
            response = input(f"⚠️ WARNING: This will delete ALL data in '{stream_name}'. Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled.")
                return False
        
        try:
            # Delete the stream completely
            result = self.redis_manager.redis_client.delete(stream_name)
            if result:
                print(f"✅ Stream '{stream_name}' cleared successfully.")
                return True
            else:
                print(f"ℹ️ Stream '{stream_name}' was already empty or didn't exist.")
                return True
        except Exception as e:
            print(f"❌ Error clearing stream '{stream_name}': {e}")
            return False
    
    def recreate_consumer_groups(self, stream_name: str, groups: list[tuple[str, str]]):
        """
        Recreate consumer groups for a stream.
        groups: List of (group_name, description) tuples
        """
        for group_name, description in groups:
            try:
                self.redis_manager.create_consumer_group(stream_name, group_name)
                print(f"✅ Recreated consumer group '{group_name}' for {description}")
            except Exception as e:
                print(f"⚠️ Error recreating group '{group_name}': {e}")
    
    def get_stream_info(self, stream_name: str):
        """Get information about a stream."""
        try:
            length = self.redis_manager.redis_client.xlen(stream_name)
            print(f"📊 Stream '{stream_name}' length: {length}")
            
            # Get consumer groups
            try:
                groups = self.redis_manager.redis_client.xinfo_groups(stream_name)
                print(f"👥 Consumer groups: {len(groups)}")
                for group in groups:
                    print(f"  - {group['name']}: {group['consumers']} consumers, {group['pending']} pending")
            except Exception as e:
                print(f"ℹ️ No consumer groups: {e}")
                
        except Exception as e:
            print(f"❌ Error getting stream info for '{stream_name}': {e}")
    
    def fix_market_events_stream(self):
        """
        Complete recovery procedure for market_events_stream issues.
        """
        print("🔧 Starting market_events_stream recovery...")
        
        # Clear the problematic stream
        if self.clear_stream("market_events_stream"):
            # Recreate consumer groups
            groups = [
                ("similarity_group", "Market Similarity Service"),
            ]
            self.recreate_consumer_groups("market_events_stream", groups)
            print("✅ market_events_stream recovery complete!")
            print("ℹ️ The market poller will recreate the stream with correct format on next run.")
        else:
            print("❌ Recovery failed.")
    
    def reset_all_streams(self):
        """Nuclear option: Reset all streams."""
        streams = [
            "market_events_stream",
            "similar_market_pairs_stream", 
            "arbitrage_opportunities_stream"
        ]
        
        print("🚨 WARNING: This will delete ALL stream data!")
        response = input("Type 'RESET_ALL' to confirm: ")
        if response != 'RESET_ALL':
            print("❌ Operation cancelled.")
            return
        
        for stream in streams:
            self.clear_stream(stream, confirm=True)
        
        # Recreate consumer groups
        self.recreate_consumer_groups("market_events_stream", [("similarity_group", "Market Similarity")])
        self.recreate_consumer_groups("similar_market_pairs_stream", [("arbitrage_group", "Arbitrage Finder")])
        self.recreate_consumer_groups("arbitrage_opportunities_stream", [
            ("trade_execution_group", "Real Trade Executor"),
            ("mock_trade_execution_group", "Mock Trade Executor")
        ])
        
        print("✅ All streams reset! Services will recreate data on next run.")

def main():
    parser = argparse.ArgumentParser(description="Redis Stream Recovery Tools")
    parser.add_argument("command", choices=[
        "info", "clear", "fix-market-events", "reset-all"
    ], help="Recovery command to execute")
    parser.add_argument("--stream", help="Stream name (for info/clear commands)")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    recovery = StreamRecovery()
    
    if args.command == "info":
        if not args.stream:
            print("❌ --stream required for info command")
            return 1
        recovery.get_stream_info(args.stream)
    
    elif args.command == "clear":
        if not args.stream:
            print("❌ --stream required for clear command")
            return 1
        recovery.clear_stream(args.stream, args.confirm)
    
    elif args.command == "fix-market-events":
        recovery.fix_market_events_stream()
    
    elif args.command == "reset-all":
        recovery.reset_all_streams()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
