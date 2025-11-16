import time
import os
import signal
import asyncio
import concurrent.futures
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform
from db.DBManager import DBManager
from cache.RedisManager import RedisManager
from utils.startup_coordinator import StartupCoordinator

class MarketPollingService:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.db_manager = DBManager()
        self.platforms = [
            KalshiPlatform(),
            PolyMarketPlatform()
        ]
        self.stream_name = "market_events_stream"
        self.shutdown_requested = False
        self.is_initial_load = True  # Flag for aggressive initial loading
        self.startup_coordinator = StartupCoordinator()
        self.existing_market_ids = set()  # Track loaded markets to avoid duplicates
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, signum, frame):
        """Gracefully handle shutdown requests."""
        print(f"Shutdown requested by signal {signum}. Finishing current cycle...")
        self.shutdown_requested = True

    def _get_platform_name(self, platform):
        """Get the display name for a platform."""
        if hasattr(platform, 'PLATFORM'):
            return platform.PLATFORM.value
        elif isinstance(platform, KalshiPlatform):
            return "Kalshi"
        elif isinstance(platform, PolyMarketPlatform):
            return "PolyMarket"
        return "Unknown"

    def _load_existing_market_ids(self):
        """Load existing market IDs from database to avoid duplicates"""
        try:
            existing_markets = self.db_manager.supabase.table('markets').select('market_id').execute()
            self.existing_market_ids = {market['market_id'] for market in existing_markets.data}
            print(f"📋 Loaded {len(self.existing_market_ids)} existing market IDs to avoid duplicates")
        except Exception as e:
            print(f"⚠️ Warning: Could not load existing market IDs: {e}")
            self.existing_market_ids = set()

    def _poll_platform_markets(self, platform, is_bulk_load=False):
        """Poll markets from a single platform."""
        platform_name = self._get_platform_name(platform)
        try:
            # Determine number of markets to fetch
            if is_bulk_load:
                # Aggressive initial load - get ALL available markets
                num_markets = 5000  
                print(f"🚀 BULK LOAD: Fetching ALL markets from {platform_name}...")
            elif self.is_initial_load:
                num_markets = 1000
                print(f"📡 INITIAL: Fetching up to {num_markets} markets from {platform_name}...")
            else:
                num_markets = 200
                print(f"🔄 POLLING: Fetching up to {num_markets} new markets from {platform_name}...")
            
            market_ids = platform.find_new_markets(num_markets)
            print(f"🎯 Found {len(market_ids)} market IDs from {platform_name}")
            
            if not market_ids:
                print(f"⚠️  No markets returned from {platform_name}")
                return 0
            
            # Filter out duplicates if not bulk loading
            if not is_bulk_load:
                original_count = len(market_ids)
                market_ids = [mid for mid in market_ids if mid not in self.existing_market_ids]
                if len(market_ids) < original_count:
                    print(f"🔍 Filtered out {original_count - len(market_ids)} duplicate markets")
            
            if not market_ids:
                print(f"✅ No new markets to process from {platform_name}")
                return 0
            
            markets = platform.get_markets(market_ids)
            print(f"📊 Retrieved {len(markets)} market details from {platform_name}")
            
            # Save markets to database first
            if markets:
                try:
                    # For bulk loads, use smaller chunks to avoid timeouts
                    if is_bulk_load and len(markets) > 500:
                        print(f"📦 Bulk saving {len(markets)} markets in chunks from {platform_name}...")
                        chunk_size = 500
                        for i in range(0, len(markets), chunk_size):
                            chunk = markets[i:i + chunk_size]
                            self.db_manager.add_markets(chunk, chunk_size=100)
                            print(f"💾 Saved chunk {i//chunk_size + 1}/{(len(markets) + chunk_size - 1)//chunk_size} ({len(chunk)} markets) from {platform_name}")
                    else:
                        self.db_manager.add_markets(markets)
                        print(f"💾 Saved {len(markets)} markets to database from {platform_name}")
                except Exception as e:
                    print(f"❌ Error saving markets to database: {e}")
            
            # Then stream to Redis for downstream processing
            markets_streamed = 0
            for market in markets:
                try:
                    # Add to our tracking set
                    if not is_bulk_load:
                        self.existing_market_ids.add(market.market_id)
                    
                    market_data = {
                        "market_id": market.market_id,
                        "platform": market.platform.value,
                        "name": market.name,
                        "rules": market.rules,
                        "close_timestamp": market.close_timestamp
                    }
                    self.redis_manager.add_to_stream(self.stream_name, market_data)
                    markets_streamed += 1
                except Exception as e:
                    print(f"❌ Error streaming market {market.market_id}: {e}")
            
            print(f"✅ Successfully saved and streamed {markets_streamed} markets from {platform_name}")
            return markets_streamed
            
        except Exception as e:
            print(f"❌ Error polling from {platform_name}: {e}")
            return 0

    def perform_bulk_load(self):
        """
        Perform initial bulk load of ALL markets from all platforms.
        """
        print("🚀 Starting BULK LOAD of all markets...")
        self.startup_coordinator.set_startup_phase("market_poller", "bulk_loading")
        
        # Load existing markets to avoid duplicates
        self._load_existing_market_ids()
        
        # Sequential bulk loading to avoid overwhelming the database
        total_markets = 0
        for platform in self.platforms:
            platform_name = self._get_platform_name(platform)
            try:
                print(f"🔄 Starting bulk load for {platform_name}...")
                markets_count = self._poll_platform_markets(platform, is_bulk_load=True)
                total_markets += markets_count
                print(f"✅ Completed bulk load for {platform_name}: {markets_count} markets")
            except Exception as e:
                print(f"❌ Platform {platform_name} failed during bulk load: {e}")
        
        print(f"🎉 Bulk load complete! Total markets streamed: {total_markets}")
        
        # Signal completion
        self.startup_coordinator.set_initial_load_complete("market_poller", total_markets)
        self.startup_coordinator.set_startup_phase("market_poller", "ready_for_polling")
        
        return total_markets

    def poll_markets(self):
        """
        Polls for markets from all platforms in parallel and adds them to Redis Stream.
        """
        print("🔄 Starting incremental market polling...")
        
        # Use ThreadPoolExecutor for parallel platform polling
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.platforms)) as executor:
            # Submit all platform polling tasks
            future_to_platform = {
                executor.submit(self._poll_platform_markets, platform): platform 
                for platform in self.platforms
            }
            
            total_markets = 0
            for future in concurrent.futures.as_completed(future_to_platform):
                platform = future_to_platform[future]
                platform_name = self._get_platform_name(platform)
                try:
                    markets_count = future.result()
                    total_markets += markets_count
                except Exception as e:
                    print(f"❌ Platform {platform_name} failed with exception: {e}")
        
        print(f"✅ Incremental polling complete! New markets streamed: {total_markets}")
        
        # After first successful load, switch to normal mode
        if self.is_initial_load:
            self.is_initial_load = False
            print("🔄 Switching from initial load mode to normal polling mode")

    def run(self):
        """
        Runs the polling service with proper startup sequence.
        """
        # Configuration
        initial_interval = int(os.getenv("INITIAL_POLLING_INTERVAL_S", 15))
        normal_interval = int(os.getenv("POLLING_INTERVAL_S", 60))
        bulk_load_enabled = os.getenv("ENABLE_BULK_LOAD", "true").lower() == "true"
        
        print(f"🚀 Starting Market Polling Service...")
        print(f"📊 Bulk load enabled: {bulk_load_enabled}")
        print(f"⏰ Initial interval: {initial_interval}s, Normal interval: {normal_interval}s")
        
        self.startup_coordinator.set_startup_phase("market_poller", "initializing")
        
        try:
            # Phase 1: Bulk load if enabled
            if bulk_load_enabled:
                print(f"📥 Phase 1: Performing bulk data load...")
                total_loaded = self.perform_bulk_load()
                print(f"✅ Bulk load complete: {total_loaded} markets loaded")
                
                # Brief pause before starting polling
                if not self.shutdown_requested:
                    print("⏸️  Brief pause before starting polling...")
                    time.sleep(5)
            else:
                print("⏭️  Skipping bulk load (disabled)")
                self.startup_coordinator.set_initial_load_complete("market_poller", 0)
            
            # Phase 2: Signal ready and start polling
            self.startup_coordinator.signal_service_ready("market_poller")
            print("🔄 Starting continuous polling mode...")
            
            # Load existing market IDs for duplicate detection
            self._load_existing_market_ids()
            
            while not self.shutdown_requested:
                self.poll_markets()
                
                # Use different intervals based on mode
                current_interval = initial_interval if self.is_initial_load else normal_interval
                
                if not self.shutdown_requested:
                    print(f"⏰ Sleeping for {current_interval} seconds...")
                    time.sleep(current_interval)
                    
        except Exception as e:
            print(f"❌ Fatal error in market polling service: {e}")
            self.startup_coordinator.set_startup_phase("market_poller", "failed")
            raise
                
        print("Market Polling Service shut down gracefully.")

if __name__ == '__main__':
    polling_service = MarketPollingService()
    polling_service.run()
