#!/usr/bin/env python3
"""
Depth Chart Visualization for Order Book Data

This script creates depth charts showing cumulative bid and ask quantities 
at each price level for Yes/No contracts on prediction markets.

The depth chart provides:
- X-axis: Price (normalized 0-1.00)
- Y-axis: Cumulative quantity
- Lines for Yes/No Bids and Asks with cumulative sums
- Interactive tooltips and market insights

Run from the project root directory:
    python -m backend.tests.test_depth_chart
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import platform classes
from backend.platform.KalshiPlatform import KalshiPlatform
from backend.platform.TestPlatform import TestPlatform
from backend.platform.PolyMarketPlatform import PolyMarketPlatform
from backend.models.Market import Market
from backend.models.Orderbook import Orderbook
from backend.models.PlatformType import PlatformType


class DepthChartVisualizer:
    """Creates depth chart visualizations for order book data."""
    
    def __init__(self):
        """Initialize the visualizer with platform instances."""
        self.platforms = {
            PlatformType.KALSHI: KalshiPlatform(),
            PlatformType.TEST: TestPlatform(),
            PlatformType.POLYMARKET: PolyMarketPlatform()
        }
    
    def normalize_price(self, price: float) -> float:
        return price /1000
    
    def calculate_cumulative_depth(self, prices: List[float], quantities: List[float], 
                                  is_bid: bool = True) -> Tuple[List[float], List[float]]:
        """
        Calculate cumulative depth for bids or asks.
        
        Args:
            prices: List of price levels
            quantities: List of quantities at each price level
            is_bid: True for bids (cumulative left to right), False for asks (right to left)
            
        Returns:
            Tuple of (sorted_prices, cumulative_quantities)
        """
        if not prices or not quantities:
            return [], []
        
        # Combine prices and quantities, then sort
        price_qty_pairs = list(zip(prices, quantities))
        
        if is_bid:
            # For bids: sort descending (highest price first), cumulate left to right
            price_qty_pairs.sort(key=lambda x: x[0], reverse=True)
        else:
            # For asks: sort ascending (lowest price first), cumulate left to right
            price_qty_pairs.sort(key=lambda x: x[0])
        
        sorted_prices = [pair[0] for pair in price_qty_pairs]
        sorted_quantities = [pair[1] for pair in price_qty_pairs]
        
        # Calculate cumulative quantities
        cumulative_quantities = []
        cumsum = 0
        for qty in sorted_quantities:
            cumsum += qty
            cumulative_quantities.append(cumsum)
        
        return sorted_prices, cumulative_quantities
    
    def calculate_market_metrics(self, orderbook: Orderbook) -> Dict[str, Any]:
        """
        Calculate key market metrics from order book data.
        
        Args:
            orderbook: Order book data
            
        Returns:
            Dictionary of market metrics
        """
        metrics = {
            'yes_best_bid': None,
            'yes_best_ask': None,
            'no_best_bid': None,
            'no_best_ask': None,
            'yes_spread': None,
            'no_spread': None,
            'total_yes_bid_volume': 0,
            'total_yes_ask_volume': 0,
            'total_no_bid_volume': 0,
            'total_no_ask_volume': 0,
            'implied_probability': None
        }
        
        # Yes contract metrics
        if orderbook.yes:
            yes_bid_prices = orderbook.yes.get('bid', [[], []])[0]
            yes_bid_quantities = orderbook.yes.get('bid', [[], []])[1]
            yes_ask_prices = orderbook.yes.get('ask', [[], []])[0]
            yes_ask_quantities = orderbook.yes.get('ask', [[], []])[1]
            
            if yes_bid_prices:
                metrics['yes_best_bid'] = max(yes_bid_prices)
                metrics['total_yes_bid_volume'] = sum(yes_bid_quantities)
            
            if yes_ask_prices:
                metrics['yes_best_ask'] = min(yes_ask_prices)
                metrics['total_yes_ask_volume'] = sum(yes_ask_quantities)
            
            if metrics['yes_best_bid'] and metrics['yes_best_ask']:
                metrics['yes_spread'] = metrics['yes_best_ask'] - metrics['yes_best_bid']
        
        # No contract metrics
        if orderbook.no:
            no_bid_prices = orderbook.no.get('bid', [[], []])[0]
            no_bid_quantities = orderbook.no.get('bid', [[], []])[1]
            no_ask_prices = orderbook.no.get('ask', [[], []])[0]
            no_ask_quantities = orderbook.no.get('ask', [[], []])[1]
            
            if no_bid_prices:
                metrics['no_best_bid'] = max(no_bid_prices)
                metrics['total_no_bid_volume'] = sum(no_bid_quantities)
            
            if no_ask_prices:
                metrics['no_best_ask'] = min(no_ask_prices)
                metrics['total_no_ask_volume'] = sum(no_ask_quantities)
            
            if metrics['no_best_bid'] and metrics['no_best_ask']:
                metrics['no_spread'] = metrics['no_best_ask'] - metrics['no_best_bid']
        
        # Calculate implied probability (midpoint of Yes contract)
        if metrics['yes_best_bid'] and metrics['yes_best_ask']:
            yes_mid = (metrics['yes_best_bid'] + metrics['yes_best_ask']) / 2
            metrics['implied_probability'] = self.normalize_price(yes_mid)
        
        return metrics
    
    def plot_depth_chart(self, market: Market, orderbook: Orderbook, ax) -> None:
        """
        Plot cumulative depth chart for a single market.
        
        Args:
            market: Market object with name and platform info
            orderbook: Order book data
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
        
        # Normalize prices
    
        if yes_bid_prices:
            yes_bid_prices = [self.normalize_price(p) for p in yes_bid_prices]
        if yes_ask_prices:
            yes_ask_prices = [self.normalize_price(p) for p in yes_ask_prices]
        if no_bid_prices:
            no_bid_prices = [self.normalize_price(p) for p in no_bid_prices]
        if no_ask_prices:
            no_ask_prices = [self.normalize_price(p) for p in no_ask_prices]
        
        # Calculate and plot cumulative depth
        yes_bid_cum_prices, yes_bid_cum_qtys = self.calculate_cumulative_depth(
            yes_bid_prices, yes_bid_quantities, is_bid=True)
        yes_ask_cum_prices, yes_ask_cum_qtys = self.calculate_cumulative_depth(
            yes_ask_prices, yes_ask_quantities, is_bid=False)
        no_bid_cum_prices, no_bid_cum_qtys = self.calculate_cumulative_depth(
            no_bid_prices, no_bid_quantities, is_bid=True)
        no_ask_cum_prices, no_ask_cum_qtys = self.calculate_cumulative_depth(
            no_ask_prices, no_ask_quantities, is_bid=False)
        
        # Plot cumulative depth curves
        if yes_bid_cum_prices:
            ax.plot(yes_bid_cum_prices, yes_bid_cum_qtys, 
                   color='#2E8B57', linewidth=3, alpha=0.8, label='Yes Bids (Cumulative)')
            ax.fill_between(yes_bid_cum_prices, yes_bid_cum_qtys, alpha=0.2, color='#2E8B57')
        
        if yes_ask_cum_prices:
            ax.plot(yes_ask_cum_prices, yes_ask_cum_qtys, 
                   color='#DC143C', linewidth=3, alpha=0.8, label='Yes Asks (Cumulative)')
            ax.fill_between(yes_ask_cum_prices, yes_ask_cum_qtys, alpha=0.2, color='#DC143C')
        
        if no_bid_cum_prices:
            ax.plot(no_bid_cum_prices, no_bid_cum_qtys, 
                   color='#228B22', linewidth=3, alpha=0.8, linestyle='--', label='No Bids (Cumulative)')
            ax.fill_between(no_bid_cum_prices, no_bid_cum_qtys, alpha=0.15, color='#228B22')
        
        if no_ask_cum_prices:
            ax.plot(no_ask_cum_prices, no_ask_cum_qtys, 
                   color='#B22222', linewidth=3, alpha=0.8, linestyle='--', label='No Asks (Cumulative)')
            ax.fill_between(no_ask_cum_prices, no_ask_cum_qtys, alpha=0.15, color='#B22222')
        
        # Calculate and display market metrics
        metrics = self.calculate_market_metrics(orderbook)
        
        # Add vertical line for implied probability
        if metrics['implied_probability'] is not None:
            ax.axvline(x=metrics['implied_probability'], color='black', linestyle=':', 
                      alpha=0.7, linewidth=2, label=f"Implied P = {metrics['implied_probability']:.3f}")
        
        # Set title and labels
        title = f"{market.name}"
        if len(title) > 60:
            title = title[:57] + "..."
        
        ax.set_title(f"{title}\nDepth Chart - {market.platform.value}", 
                    fontsize=11, fontweight='bold', pad=20)
        
        ax.set_xlabel('Price (Probability)', fontsize=10)
        ax.set_ylabel('Cumulative Quantity', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Format x-axis as percentages
        ax.set_xlim(0, 1)
        ax.set_xticks(np.arange(0, 1.1, 0.2))
        ax.set_xticklabels([f"{int(x*100)}%" for x in np.arange(0, 1.1, 0.2)])
        
        # Add legend
        ax.legend(fontsize=8, loc='upper right')
        
        # Add metrics text box
        metrics_text = []
        if metrics['yes_best_bid'] and metrics['yes_best_ask']:
            yes_spread_pct = (metrics['yes_spread'] / max(metrics['yes_best_bid'], 0.01)) * 100
            metrics_text.append(f"Yes Spread: {metrics['yes_spread']:.3f} ({yes_spread_pct:.1f}%)")
        
        if metrics['no_best_bid'] and metrics['no_best_ask']:
            no_spread_pct = (metrics['no_spread'] / max(metrics['no_best_bid'], 0.01)) * 100
            metrics_text.append(f"No Spread: {metrics['no_spread']:.3f} ({no_spread_pct:.1f}%)")
        
        total_volume = (metrics['total_yes_bid_volume'] + metrics['total_yes_ask_volume'] + 
                       metrics['total_no_bid_volume'] + metrics['total_no_ask_volume'])
        if total_volume > 0:
            metrics_text.append(f"Total Volume: {total_volume:.0f}")
        
        if metrics_text:
            ax.text(0.02, 0.98, '\n'.join(metrics_text), transform=ax.transAxes, 
                   fontsize=8, verticalalignment='top', bbox=dict(boxstyle='round', 
                   facecolor='white', alpha=0.8))
    
    def get_platform_data(self, platform_type: PlatformType, num_markets: int = 1) -> Tuple[List[Market], List[Orderbook]]:
        """
        Get market and order book data from a platform.
        
        Args:
            platform_type: PlatformType enum value
            num_markets: Number of markets to fetch
            
        Returns:
            Tuple of (markets, orderbooks)
        """
        if platform_type not in self.platforms:
            print(f"Unknown platform: {platform_type}")
            return [], []
        
        platform = self.platforms[platform_type]
        print(f"Fetching {num_markets} market(s) from {platform_type.value}...")
        
        try:
            # Get market IDs
            market_ids = platform.find_new_markets(num_markets)
            if not market_ids:
                print(f"No market IDs found for {platform_type.value}")
                return [], []
            
            print(f"Found market IDs: {market_ids}")
            
            # Get market details
            markets = platform.get_markets(market_ids)
            print(f"Retrieved {len(markets)} market(s)")
            
            # Get order books
            orderbooks = platform.get_order_books(market_ids)
            print(f"Retrieved {len(orderbooks)} order book(s)")
            
            return markets, orderbooks
            
        except Exception as e:
            print(f"Error fetching data from {platform_type.value}: {e}")
            import traceback
            traceback.print_exc()
            return [], []
    
    def create_depth_chart_comparison(self, platform_types: List[PlatformType] = None, 
                                    num_markets: int = 1,
                                    save_to_file: bool = False, filename: str = None) -> None:
        """
        Create depth chart comparison across multiple platforms.
        
        Args:
            platform_types: List of PlatformType enum values to compare
            num_markets: Number of markets per platform
            save_to_file: If True, save plot to file
            filename: Optional filename for saving
        """
        if platform_types is None:
            platform_types = [PlatformType.KALSHI, PlatformType.TEST, PlatformType.POLYMARKET]
        
        print("=== Depth Chart Visualization Starting ===")
        
        # Collect data from platforms
        all_data = []
        for platform_type in platform_types:
            markets, orderbooks = self.get_platform_data(platform_type, num_markets)
            if markets and orderbooks:
                for market, orderbook in zip(markets, orderbooks):
                    all_data.append((platform_type, market, orderbook))
        
        if not all_data:
            print("No data available for depth chart visualization!")
            return
        
        print(f"Creating depth charts for {len(all_data)} market(s)...")
        
        # Create subplot grid
        cols = min(3, len(all_data))
        rows = (len(all_data) + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(7 * cols, 6 * rows))
        fig.suptitle('Market Depth Chart Comparison - Prediction Markets', 
                    fontsize=16, fontweight='bold')
        
        # Handle single subplot case
        if len(all_data) == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes if cols > 1 else [axes]
        else:
            axes = axes.flatten()
        
        # Plot each market
        for idx, (platform_type, market, orderbook) in enumerate(all_data):
            if idx < len(axes):
                print(f"  Plotting {platform_type.value}: {market.name[:30]}...")
                self.plot_depth_chart(market, orderbook, axes[idx])
        
        # Hide unused subplots
        for idx in range(len(all_data), len(axes)):
            axes[idx].set_visible(False)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)
        
        # Save or show
        if save_to_file:
            if filename is None:
                test_dir = os.path.dirname(os.path.abspath(__file__))
                filename = os.path.join(test_dir, "depth_chart_visualization.png")
            elif not os.path.isabs(filename):
                test_dir = os.path.dirname(os.path.abspath(__file__))
                filename = os.path.join(test_dir, filename)
            
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Depth chart saved to {filename}")
        else:
            plt.show()
        
        print("=== Depth Chart Visualization Complete ===")


def test_depth_chart():
    """Test function for depth chart visualization."""
    try:
        visualizer = DepthChartVisualizer()
        
        # Test cumulative depth chart
        print("Testing cumulative depth chart...") 
        visualizer.create_depth_chart_comparison(
            platform_types=[PlatformType.KALSHI, PlatformType.POLYMARKET], 
            num_markets=3,
            save_to_file=True, 
            filename="test_depth_chart_cumulative.png"
        )
        
        print("✅ Depth chart test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in depth chart test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run depth chart visualization."""
    try:
        visualizer = DepthChartVisualizer()
        
        # Create cumulative depth chart
        print("Creating depth chart visualization...")
        visualizer.create_depth_chart_comparison(
            platform_types=[PlatformType.KALSHI, PlatformType.TEST, PlatformType.POLYMARKET],
            num_markets=1,
            save_to_file=False
        )
        
    except Exception as e:
        print(f"Error running depth chart visualization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run test by default, or main for interactive display
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        main()
    else:
        test_depth_chart()
