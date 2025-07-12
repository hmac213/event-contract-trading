#!/usr/bin/env python3
"""
Platform Grapher Test - Visualizes order book data from different trading platforms.

This script creates graphs showing bid/ask data for markets from:
- KalshiPlatform
- TestPlatform  
- PolyMarketPlatform

Each graph shows:
- Yes bids (green)
- Yes asks (red)  
- No bids (green)
- No asks (red)

Run from the project root directory:
    python -m backend.tests.test_platform_grapher
"""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Any
import numpy as np

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import platform classes
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.TestPlatform import TestPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.platform.BasePlatform import PlatformType
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook


class PlatformGrapher:
    """Creates visualizations of order book data from different platforms."""
    
    def __init__(self):
        """Initialize the grapher with platform instances."""
        self.kalshi_platform = KalshiPlatform()
        self.test_platform = TestPlatform()
        self.polymarket_platform = PolyMarketPlatform()
    
    def get_platform_data(self, platform, platform_name: str, num_markets: int = 3) -> tuple[List[Market], List[Orderbook]]:
        """
        Get market and orderbook data from a platform.
        
        Args:
            platform: Platform instance
            platform_name: Name of the platform for logging
            num_markets: Number of markets to fetch
            
        Returns:
            Tuple of (markets, orderbooks)
        """
        print(f"Fetching {num_markets} markets from {platform_name}...")
        
        try:
            # Get market IDs
            market_ids = platform.find_new_markets(num_markets)
            if not market_ids:
                print(f"No market IDs found for {platform_name}")
                return [], []
            
            print(f"Found market IDs: {market_ids}")
            
            # Get market details
            markets = platform.get_markets(market_ids)
            print(f"Retrieved {len(markets)} markets")
            
            # Get order books
            orderbooks = platform.get_order_books(market_ids)
            print(f"Retrieved {len(orderbooks)} orderbooks")
            
            return markets, orderbooks
            
        except Exception as e:
            print(f"Error fetching data from {platform_name}: {e}")
            return [], []
    
    def plot_orderbook(self, market: Market, orderbook: Orderbook, ax):
        """
        Plot order book data for a single market.
        
        Args:
            market: Market object with name and platform info
            orderbook: Orderbook object with bid/ask data
            ax: Matplotlib axis to plot on
        """
        # Extract data
        yes_bid_prices = orderbook.yes.get('bid', [[], []])[0] if orderbook.yes else []
        yes_bid_quantities = orderbook.yes.get('bid', [[], []])[1] if orderbook.yes else []
        yes_ask_prices = orderbook.yes.get('ask', [[], []])[0] if orderbook.yes else []
        yes_ask_quantities = orderbook.yes.get('ask', [[], []])[1] if orderbook.yes else []
        
        no_bid_prices = orderbook.no.get('bid', [[], []])[0] if orderbook.no else []
        no_bid_quantities = orderbook.no.get('bid', [[], []])[1] if orderbook.no else []
        no_ask_prices = orderbook.no.get('ask', [[], []])[0] if orderbook.no else []
        no_ask_quantities = orderbook.no.get('ask', [[], []])[1] if orderbook.no else []
        
        # Plot YES bids (green) and asks (red)
        if yes_bid_prices and yes_bid_quantities:
            ax.scatter(yes_bid_prices, yes_bid_quantities, 
                      color='green', alpha=0.7, s=30, label='Yes Bids')
        
        if yes_ask_prices and yes_ask_quantities:
            ax.scatter(yes_ask_prices, yes_ask_quantities, 
                      color='red', alpha=0.7, s=30, label='Yes Asks')
        
        # Plot NO bids (dark green) and asks (dark red)
        if no_bid_prices and no_bid_quantities:
            ax.scatter(no_bid_prices, no_bid_quantities, 
                      color='darkgreen', alpha=0.7, s=30, marker='^', label='No Bids')
        
        if no_ask_prices and no_ask_quantities:
            ax.scatter(no_ask_prices, no_ask_quantities, 
                      color='darkred', alpha=0.7, s=30, marker='^', label='No Asks')
        
        # Set title and labels
        title = f"{market.name} - {market.platform.value}"
        # Truncate long titles
        if len(title) > 50:
            title = title[:47] + "..."
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xlabel('Price')
        ax.set_ylabel('Quantity')
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend(fontsize=8)
        
    def create_visualization(self, save_to_file: bool = False, filename: str = None):
        """
        Create the complete visualization with data from all platforms.
        
        Args:
            save_to_file: If True, save the plot to a file instead of showing it
            filename: Optional filename for saving the plot
        """
        print("=== Platform Grapher Starting ===")
        
        # Collect data from all platforms
        platforms_data = []
        NUM_MARKETS = 5 
        # Kalshi Platform
        kalshi_markets, kalshi_orderbooks = self.get_platform_data(
            self.kalshi_platform, "KalshiPlatform", NUM_MARKETS)
        platforms_data.append(("Kalshi", kalshi_markets, kalshi_orderbooks))
        
        # Test Platform 
        test_markets, test_orderbooks = self.get_platform_data(
            self.test_platform, "TestPlatform", NUM_MARKETS)
        platforms_data.append(("Test", test_markets, test_orderbooks))
        
        # PolyMarket Platform
        polymarket_markets, polymarket_orderbooks = self.get_platform_data(
            self.polymarket_platform, "PolyMarketPlatform", NUM_MARKETS)
        platforms_data.append(("PolyMarket", polymarket_markets, polymarket_orderbooks))
        
        # Count total markets to plot
        total_markets = sum(len(markets) for _, markets, _ in platforms_data)
        if total_markets == 0:
            print("No markets to plot!")
            return
        
        print(f"Total markets to plot: {total_markets}")
        
        # Create subplot grid
        cols = NUM_MARKETS
        rows = max(1, (total_markets + cols - 1) // cols)  # Ceiling division
        
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
        fig.suptitle('Order Book Data from Multiple Platforms', fontsize=16, fontweight='bold')
        
        # Handle case where we have only one row
        if rows == 1:
            axes = axes if total_markets > 1 else [axes]
        else:
            axes = axes.flatten()
        
        # Plot each market
        plot_idx = 0
        for platform_name, markets, orderbooks in platforms_data:
            print(f"\nPlotting {len(markets)} markets from {platform_name}...")
            
            for i, (market, orderbook) in enumerate(zip(markets, orderbooks)):
                if plot_idx < len(axes):
                    print(f"  Plotting market {i+1}: {market.name[:30]}...")
                    self.plot_orderbook(market, orderbook, axes[plot_idx])
                    plot_idx += 1
        
        # Hide unused subplots
        for i in range(plot_idx, len(axes)):
            axes[i].set_visible(False)
        
        # Adjust layout and show
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)  # Make room for suptitle
        
        # Create custom legend for the entire figure
        legend_elements = [
            mpatches.Patch(color='green', label='Yes Bids'),
            mpatches.Patch(color='red', label='Yes Asks'),
            mpatches.Patch(color='darkgreen', label='No Bids'),
            mpatches.Patch(color='darkred', label='No Asks')
        ]
        fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
        
        if save_to_file:
            if filename is None:
                # Default to saving in the test directory
                test_dir = os.path.dirname(os.path.abspath(__file__))
                filename = os.path.join(test_dir, f"platform_orderbooks_{total_markets}_markets.png")
            elif not os.path.isabs(filename):
                # If filename is relative, save it in the test directory
                test_dir = os.path.dirname(os.path.abspath(__file__))
                filename = os.path.join(test_dir, filename)
            
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Visualization saved to {filename}")
        else:
            print(f"\nShowing visualization with {plot_idx} markets...")
            plt.show()
        
        print("=== Platform Grapher Complete ===")


def test_platform_grapher():
    """Test function to run the platform grapher."""
    try:
        grapher = PlatformGrapher()
        # Get the directory where this test file is located
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_filename = os.path.join(test_dir, "test_platform_visualization.png")
        
        # Save to file instead of showing for testing
        grapher.create_visualization(save_to_file=True, filename=test_filename)
        print("✅ Platform grapher test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running platform grapher: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the platform grapher."""
    try:
        grapher = PlatformGrapher()
        grapher.create_visualization(save_to_file=False)  # Show the plot
    except Exception as e:
        print(f"Error running platform grapher: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_platform_grapher()
