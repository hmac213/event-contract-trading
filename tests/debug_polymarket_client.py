import os
import logging
from dotenv import load_dotenv
import requests
import json
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY

# --- SETUP ---
# This script is for debugging the 'invalid signature' error from PolyMarket.
# It isolates the py_clob_client from the rest of the application to test
# the API key and environment setup in the most direct way possible.
#
# To run:
# 1. Make sure your .env file has PRIVATE_KEY and PROXY_ADDRESS set.
# 2. Run this file directly: python -m backend.tests.debug_polymarket_client
#
# If this script fails with 'invalid signature', it points to an issue with
# the API keys or the py_clob_client library version, not the application code.
# If it succeeds, there is a subtle bug in how PolyMarketPlatform.py uses the client.
# ---

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
load_dotenv()

def debug_polymarket():
    logging.info("--- Starting PolyMarket CLOB Client Debug Test ---")

    # --- Client Initialization ---
    try:
        host: str = "https://clob.polymarket.com"
        key: str = os.getenv("PRIVATE_KEY")
        funder: str = os.getenv("PROXY_ADDRESS")
        chain_id: int = 137
        
        if not key or not funder:
            logging.error("PRIVATE_KEY and PROXY_ADDRESS must be set in your .env file.")
            return

        # Using signature_type=1, which corresponds to an Email/Magic link account (like Google sign-in)
        client = ClobClient(host, key=key, chain_id=chain_id, signature_type=1, funder=funder)
        client.set_api_creds(client.create_or_derive_api_creds())
        logging.info("ClobClient initialized and API credentials set successfully.")
        logging.info(f"Using funder (proxy) address: {funder}")

    except Exception as e:
        logging.error(f"Failed to initialize ClobClient: {e}", exc_info=True)
        return

    # --- Order Creation ---
    try:
        # Using the same market as the main test script
        market_id = "0x310c3d08f015157ec78e04f3f4fefed659b5e2bd88ae80cb38ff27ef970c39bd"
        
        # We need the token ID for the "yes" side.
        # This is a simplified way to get it for this test.
        # A real implementation would have more robust error handling.
        gamma_url = f"https://gamma-api.polymarket.com/markets?condition_ids={market_id}"
        gamma_response = requests.get(gamma_url).json()
        
        # The API returns clobTokenIds as a string, so we must parse it.
        token_ids = json.loads(gamma_response[0]["clobTokenIds"])
        yes_token_id = token_ids[0]
        logging.info(f"Retrieved YES token ID: {yes_token_id}")

        order_args = OrderArgs(
            price=0.01,         # A price unlikely to fill, so it rests on the book
            size=5.0,           # Minimum size for PolyMarket is 5
            side=BUY,
            token_id=yes_token_id
        )
        
        logging.info(f"Creating signed order with args: price={order_args.price}, size={order_args.size}")
        signed_order = client.create_order(order_args)
        logging.info("Order signed successfully.")
        logging.info(f"Signed payload: {vars(signed_order.order)}")

    except Exception as e:
        logging.error(f"Failed during order creation/signing: {e}", exc_info=True)
        return

    # --- Order Placement ---
    try:
        logging.info("Attempting to post GTC order to PolyMarket...")
        response = client.post_order(signed_order, OrderType.GTC)
        logging.info(f"SUCCESS! Order placed successfully. Response: {response}")

    except Exception as e:
        logging.error(f"FAILED to place order. This likely confirms an environment or API key issue.", exc_info=True)

if __name__ == "__main__":
    debug_polymarket() 