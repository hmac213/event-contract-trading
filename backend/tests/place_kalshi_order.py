import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.platform.KalshiPlatform import KalshiPlatform
from backend.models.Order import Order

def place_test_order():
    """
    Places a test order on the Kalshi platform and prints the response.
    To test cancellation, we place a limit order with a price that is
    unlikely to be filled immediately.
    """
    try:
        # Make sure you have KALSHI_ACCESS_KEY and KALSHI_PRIVATE_KEY in your .env file
        platform = KalshiPlatform()
        
        # A limit order with a low price is likely to be "resting" and thus cancellable.
        test_order = Order.create_limit_buy_order(
            market_id="OAIAGI-25",
            side="yes",
            size=1,
            price=1,  # A very low price in cents to ensure it doesn't fill.
            time_in_force='GTC'
        )
        
        print(f"Placing order: {test_order.__dict__}")
        
        # Place the order
        response = platform.place_order(test_order)
        
        # Print the response
        print("Order placement response:")
        print(response)
        
        order_details = response.get('order')
        if order_details:
            order_id = order_details.get('order_id')
            order_status = order_details.get('status')
            
            # The test order now has the ID assigned by the exchange.
            test_order.id = order_id

            print(f"Successfully placed order with ID: {order_id}, Status: {order_status}")

            if order_status == 'resting':
                print("Order is resting, attempting to cancel...")
                cancel_response = platform.cancel_order(test_order)
                print("Cancellation response:")
                print(cancel_response)
            else:
                print(f"Order is not in a 'resting' state (status: {order_status}), so it cannot be cancelled.")
        else:
            print("Could not find 'order' details in the response.")


    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    place_test_order() 