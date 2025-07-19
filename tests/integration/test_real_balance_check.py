import unittest
from dotenv import load_dotenv
from platforms.KalshiPlatform import KalshiPlatform
from platforms.PolyMarketPlatform import PolyMarketPlatform

# Load environment variables from .env file
load_dotenv()

class TestRealBalanceCheck(unittest.TestCase):

    def test_display_real_balances(self):
        """
        Connects to live platforms and prints the account balances.
        """
        print("\n--- Checking Real Account Balances ---")
        
        # --- Kalshi ---
        try:
            print("Connecting to Kalshi...")
            kalshi_platform = KalshiPlatform()
            kalshi_balance = kalshi_platform.get_balance()
            print(f"✅ Kalshi Balance: ${kalshi_balance:,.2f}")
            self.assertIsInstance(kalshi_balance, float)
            self.assertGreaterEqual(kalshi_balance, 0)
        except Exception as e:
            print(f"❌ Could not retrieve Kalshi balance. Error: {e}")
            # Optionally fail the test if a connection is required
            # self.fail("Failed to connect to Kalshi.")

        print("-" * 20)

        # --- PolyMarket ---
        try:
            print("Connecting to PolyMarket (and Polygon network)...")
            polymarket_platform = PolyMarketPlatform()
            
            # This now checks the PROXY address balance directly.
            polymarket_balance = polymarket_platform.get_balance()
            print(f"✅ PolyMarket Deposited Balance (USDC): ${polymarket_balance:,.2f}")
            self.assertIsInstance(polymarket_balance, float)
            self.assertGreaterEqual(polymarket_balance, 0)

        except Exception as e:
            print(f"❌ Could not retrieve PolyMarket balance. Error: {e}")
            # Optionally fail the test if a connection is required
            # self.fail("Failed to connect to PolyMarket.")
            
        print("\n--- Balance Check Complete ---")

if __name__ == '__main__':
    unittest.main() 