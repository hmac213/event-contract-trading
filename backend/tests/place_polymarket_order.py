import sys
import os
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.models.Order import Order

def place_polymarket_test_order():
    """
    Places and then cancels a test order on the PolyMarket platform.
    """
    try:
        # Make sure you have PRIVATE_KEY and PROXY_ADDRESS in your .env file
        platform = PolyMarketPlatform()

        # 1. Find an active market to place an order on.
        print("Finding an active market on PolyMarket...")
        active_markets = platform.find_new_markets(1)
        if not active_markets:
            print("Could not find any active markets. Exiting.")
            return
        
        market_id = active_markets[0]
        print(f"Found market ID: {market_id}")

        # 2. Create a limit order that is unlikely to be filled immediately.
        # This ensures the order is "resting" and can be cancelled.
        test_order = Order.create_limit_buy_order(
            market_id=market_id,
            side="yes",
            size=1,
            price=1,  # Price in cents. This will be converted to $0.01 by the platform logic.
            time_in_force='GTC'
        )
        
        print(f"Placing order: {test_order.__dict__}")
        
        # 3. Place the order
        response = platform.place_order(test_order)
        
        print("Order placement response:")
        print(response)

        # The order ID is in the response, and is also set on our test_order object.
        if test_order.id:
            print(f"Successfully placed order with ID: {test_order.id}")
            
            # 4. Cancel the order
            print("Cancelling order...")
            # A small delay to ensure the order is settled on the books before cancellation.
            asyncio.run(asyncio.sleep(2))
            cancel_response = platform.cancel_order(test_order)
            print("Cancellation response:")
            print(cancel_response)
        else:
            print("Could not retrieve order ID from placement response.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    place_polymarket_test_order() 