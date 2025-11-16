#!/usr/bin/env python3
"""
Setup Validation Script for Mock Trading System
Checks all prerequisites and configuration before running the full pipeline
"""

import os
import sys
import traceback
from typing import Tuple, List

def check_result(success: bool, message: str) -> str:
    """Format check results with emojis."""
    return f"{'✅' if success else '❌'} {message}"

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check required environment variables."""
    results = []
    all_good = True
    
    # Core environment variables
    required_vars = {
        'SUPABASE_URL': 'Database connection',
        'SUPABASE_KEY': 'Database authentication',
        'OPENAI_API_KEY': 'AI market similarity',
        'PINECONE_API_KEY': 'Vector database for similarity',
        'PRIVATE_KEY': 'PolyMarket Web3 access',
        'PROXY_ADDRESS': 'PolyMarket proxy contract',
        'KALSHI_ACCESS_KEY': 'Kalshi API access',
        'KALSHI_PRIVATE_KEY': 'Kalshi API authentication'
    }
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            results.append(check_result(True, f"{var}: {description}"))
        else:
            results.append(check_result(False, f"{var}: {description} (MISSING)"))
            all_good = False
    
    return all_good, results

def check_database_connection() -> Tuple[bool, str]:
    """Test database connection."""
    try:
        from db.DBManager import DBManager
        db = DBManager()
        
        # Test basic connection
        response = db.supabase.table('markets').select('count', count='exact').execute()
        count = response.count if hasattr(response, 'count') else 0
        
        return True, f"Database connected (found {count} markets)"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def check_redis_connection() -> Tuple[bool, str]:
    """Test Redis connection."""
    try:
        from cache.RedisManager import RedisManager
        redis_manager = RedisManager()
        
        # Test ping
        redis_manager.redis_client.ping()
        return True, "Redis connected successfully"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"

def check_platform_apis() -> Tuple[bool, List[str]]:
    """Test platform API connections."""
    results = []
    all_good = True
    
    # Test Kalshi
    try:
        from platforms.KalshiPlatform import KalshiPlatform
        kalshi = KalshiPlatform()
        balance = kalshi.get_balance()
        results.append(check_result(True, f"Kalshi API connected (balance: ${balance:.2f})"))
    except Exception as e:
        results.append(check_result(False, f"Kalshi API failed: {str(e)}"))
        all_good = False
    
    # Test PolyMarket
    try:
        from platforms.PolyMarketPlatform import PolyMarketPlatform
        poly = PolyMarketPlatform()
        balance = poly.get_balance()
        results.append(check_result(True, f"PolyMarket API connected (balance: ${balance:.2f})"))
    except Exception as e:
        results.append(check_result(False, f"PolyMarket API failed: {str(e)}"))
        all_good = False
    
    return all_good, results

def check_ai_services() -> Tuple[bool, List[str]]:
    """Test AI service connections."""
    results = []
    all_good = True
    
    # Test OpenAI
    try:
        import openai
        client = openai.OpenAI()
        # Simple test call
        response = client.models.list()
        results.append(check_result(True, f"OpenAI API connected (found {len(response.data)} models)"))
    except Exception as e:
        results.append(check_result(False, f"OpenAI API failed: {str(e)}"))
        all_good = False
    
    # Test Pinecone
    try:
        from services.market_similarity.db.pinecone_manager import SimilarityDBManager
        pinecone_manager = SimilarityDBManager()
        results.append(check_result(True, f"Pinecone connected (index: {pinecone_manager.index_name})"))
    except Exception as e:
        results.append(check_result(False, f"Pinecone failed: {str(e)}"))
        all_good = False
    
    return all_good, results

def check_mock_database() -> Tuple[bool, str]:
    """Check mock trading database setup."""
    try:
        from services.mock_trade_executor.mock_db_manager import MockDBManager
        mock_db = MockDBManager()
        
        # Test if tables exist by trying to get balances
        stats = mock_db.get_mock_trading_stats()
        return True, f"Mock database ready (tables exist, {stats.get('total_trades', 0)} trades)"
    except Exception as e:
        return False, f"Mock database setup incomplete: {str(e)}"

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check Python package dependencies."""
    results = []
    all_good = True
    
    required_packages = [
        'supabase', 'redis', 'openai', 'pinecone', 'py_clob_client',
        'web3', 'httpx', 'aiohttp', 'cryptography', 'eth_account'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            results.append(check_result(True, f"Package {package} installed"))
        except ImportError:
            results.append(check_result(False, f"Package {package} missing"))
            all_good = False
    
    return all_good, results

def check_platform_implementations() -> Tuple[bool, List[str]]:
    """Check that all platform implementations are complete."""
    results = []
    all_good = True
    
    try:
        from platforms.TestPlatform import TestPlatform
        # Try to instantiate to check for missing abstract methods
        test_platform = TestPlatform()
        results.append(check_result(True, "TestPlatform implementation complete"))
    except TypeError as e:
        if "abstract" in str(e):
            results.append(check_result(False, f"TestPlatform missing abstract methods: {e}"))
            all_good = False
        else:
            raise
    except Exception as e:
        results.append(check_result(False, f"TestPlatform error: {e}"))
        all_good = False
    
    return all_good, results

def main():
    """Run all validation checks."""
    print("🎭 Mock Trading System Validation")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Python Dependencies", check_dependencies),
        ("Platform Implementations", check_platform_implementations),
        ("Database Connection", check_database_connection),
        ("Redis Connection", check_redis_connection),
        ("Platform APIs", check_platform_apis),
        ("AI Services", check_ai_services),
        ("Mock Database", check_mock_database),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            result = check_func()
            
            if isinstance(result, tuple) and len(result) == 2:
                if isinstance(result[1], list):
                    # Multiple results
                    success, messages = result
                    for message in messages:
                        print(f"  {message}")
                    if not success:
                        all_passed = False
                else:
                    # Single result
                    success, message = result
                    print(f"  {check_result(success, message)}")
                    if not success:
                        all_passed = False
        except Exception as e:
            print(f"  ❌ Check failed with error: {str(e)}")
            print(f"     {traceback.format_exc().splitlines()[-1]}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! Ready to run mock trading system.")
        print("\nNext steps:")
        print("1. docker-compose --profile data --profile mock-trading up")
        print("2. python services/mock_trade_executor/mock_trading_cli.py stats")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above before proceeding.")
        print("\nRefer to MOCK_TRADING_SETUP.md for detailed setup instructions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
