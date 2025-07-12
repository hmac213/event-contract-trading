#!/usr/bin/env python3
"""
Platform Grapher Bar Chart Test - Visualizes order book data using bar charts.

This script creates bar chart graphs showing bid/ask data for markets from:
- KalshiPlatform
- TestPlatform  
- PolyMarketPlatform

Each graph shows:
- Yes bids (green bars)
- Yes asks (red bars)  
- No bids (dark green bars)
- No asks (dark red bars)

Run from the project root directory:
    python -m backend.tests.test_platform_grapher_bar_chart
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


class PlatformGrapherBarChart:
    """Creates bar chart visualizations of order book data from different platforms."""
    
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
    
    def plot_orderbook_bar_chart(self, market: Market, orderbook: Orderbook, ax):
        """
        Plot order book data for a single market using bar charts.
        
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
        
        # Combine all price data to create x-axis categories
        all_prices = []
        if yes_bid_prices:
            all_prices.extend(yes_bid_prices)
        if yes_ask_prices:
            all_prices.extend(yes_ask_prices)
        if no_bid_prices:
            all_prices.extend(no_bid_prices)
        if no_ask_prices:
            all_prices.extend(no_ask_prices)
        
        if not all_prices:
            ax.text(0.5, 0.5, 'No Data Available', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(f"{market.name[:30]}... - {market.platform.value}", fontsize=10)
            return
        
        # Create sorted unique price points for x-axis
        unique_prices = sorted(set(all_prices))
        price_indices = {price: i for i, price in enumerate(unique_prices)}
        
        # Prepare data for bar chart
        bar_width = 0.2
        x_positions = np.arange(len(unique_prices))
        
        # Initialize quantity arrays
        yes_bid_qty = np.zeros(len(unique_prices))
        yes_ask_qty = np.zeros(len(unique_prices))
        no_bid_qty = np.zeros(len(unique_prices))
        no_ask_qty = np.zeros(len(unique_prices))
        
        # Fill quantity arrays
        for price, qty in zip(yes_bid_prices, yes_bid_quantities):
            yes_bid_qty[price_indices[price]] = qty
            
        for price, qty in zip(yes_ask_prices, yes_ask_quantities):
            yes_ask_qty[price_indices[price]] = qty
            
        for price, qty in zip(no_bid_prices, no_bid_quantities):
            no_bid_qty[price_indices[price]] = qty
            
        for price, qty in zip(no_ask_prices, no_ask_quantities):
            no_ask_qty[price_indices[price]] = qty
        
        # Create bar charts with offset positions
        bars1 = ax.bar(x_positions - 1.5*bar_width, yes_bid_qty, bar_width, 
                      color='green', alpha=0.7, label='Yes Bids')
        bars2 = ax.bar(x_positions - 0.5*bar_width, yes_ask_qty, bar_width, 
                      color='red', alpha=0.7, label='Yes Asks')
        bars3 = ax.bar(x_positions + 0.5*bar_width, no_bid_qty, bar_width, 
                      color='darkgreen', alpha=0.7, label='No Bids')
        bars4 = ax.bar(x_positions + 1.5*bar_width, no_ask_qty, bar_width, 
                      color='darkred', alpha=0.7, label='No Asks')
        
        # Set labels and title
        ax.set_xlabel('Price Points')
        ax.set_ylabel('Quantity')
        ax.set_xticks(x_positions)
        
        # Format x-axis labels - show only a subset if too many prices
        if len(unique_prices) > 10:
            # Show every nth price to avoid overcrowding
            step = max(1, len(unique_prices) // 10)
            tick_labels = [f'{price:.2f}' if i % step == 0 else '' for i, price in enumerate(unique_prices)]
        else:
            tick_labels = [f'{price:.2f}' for price in unique_prices]
        
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')
        
        # Set title
        title = f"{market.name} - {market.platform.value}"
        if len(title) > 50:
            title = title[:47] + "..."
        ax.set_title(title, fontsize=10, fontweight='bold')
        
        # Add grid and legend
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(fontsize=8)
        
        # Add value labels on bars (only for non-zero values)
        def add_value_labels(bars, quantities):
            for bar, qty in zip(bars, quantities):
                if qty > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{qty:.1f}', ha='center', va='bottom', fontsize=7)
        
        add_value_labels(bars1, yes_bid_qty)
        add_value_labels(bars2, yes_ask_qty)
        add_value_labels(bars3, no_bid_qty)
        add_value_labels(bars4, no_ask_qty)
        
    def create_bar_chart_visualization(self, save_to_file: bool = False, filename: str = None):
        """
        Create the complete bar chart visualization with data from all platforms.
        
        Args:
            save_to_file: If True, save the plot to a file instead of showing it
            filename: Optional filename for saving the plot
        """
        print("=== Platform Bar Chart Grapher Starting ===")
        
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
        
        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
        fig.suptitle('Order Book Data (Bar Charts) from Multiple Platforms', fontsize=16, fontweight='bold')
        
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
                    self.plot_orderbook_bar_chart(market, orderbook, axes[plot_idx])
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
                filename = os.path.join(test_dir, f"platform_orderbooks_bar_chart_{total_markets}_markets.png")
            elif not os.path.isabs(filename):
                # If filename is relative, save it in the test directory
                test_dir = os.path.dirname(os.path.abspath(__file__))
                filename = os.path.join(test_dir, filename)
            
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Bar chart visualization saved to {filename}")
        else:
            print(f"\nShowing bar chart visualization with {plot_idx} markets...")
            plt.show()
        
        print("=== Platform Bar Chart Grapher Complete ===")


def test_platform_grapher_bar_chart():
    """Test function to run the platform grapher with bar charts."""
    try:
        grapher = PlatformGrapherBarChart()
        # Get the directory where this test file is located
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_filename = os.path.join(test_dir, "test_platform_bar_chart_visualization.png")
        
        # Save to file instead of showing for testing
        grapher.create_bar_chart_visualization(save_to_file=True, filename=test_filename)
        print("✅ Platform bar chart grapher test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running platform bar chart grapher: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the platform grapher with bar charts."""
    try:
        grapher = PlatformGrapherBarChart()
        grapher.create_bar_chart_visualization(save_to_file=False)  # Show the plot
    except Exception as e:
        print(f"Error running platform bar chart grapher: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_platform_grapher_bar_chart()
