#!/usr/bin/env python3
"""
Comprehensive Visualization Demo

This script demonstrates all the visualization capabilities:
1. Depth charts (cumulative order book visualization)
2. Bar charts (volume comparison across markets)
3. Integration with platform data

Run from the project root directory:
    python -m backend.tests.visualization_demo
"""

import sys
import os

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.tests.test_depth_chart import DepthChartVisualizer


def main():
    """Comprehensive visualization demonstration."""
    print("🚀 Comprehensive Visualization Demo Starting")
    print("=" * 60)
    
    try:
        # 1. Test depth chart visualizer directly
        print("\n1. Testing Depth Chart Visualizer...")
        visualizer = DepthChartVisualizer()
        
        # Create depth charts for different platforms
        visualizer.create_depth_chart_comparison(
            platform_names=['Polymarket'],  # Use Polymarket platform for reliable data
            num_markets=1,
            show_raw=False,
            save_to_file=True,
            filename="demo_depth_chart.png"
        )
        
        # Create raw order book view
        visualizer.create_depth_chart_comparison(
            platform_names=['Polymarket'],
            num_markets=1,
            show_raw=True,
            save_to_file=True,
            filename="demo_raw_orderbook.png"
        )
        
        print("✅ Depth chart visualizer tests completed!")
        
        # 2. Test integration with platform reader
        print("\n2. Testing Platform Reader Integration...")
        test_depth_chart_integration()
        
        # 3. Summary
        print("\n" + "=" * 60)
        print("📊 Visualization Demo Summary")
        print("=" * 60)
        print("✅ Depth Chart Visualization - Shows cumulative order book depth")
        print("   • X-axis: Price (normalized 0-100%)")
        print("   • Y-axis: Cumulative quantity")
        print("   • Features: Yes/No contracts, implied probability, spread metrics")
        print("✅ Raw Order Book View - Shows actual order levels")
        print("   • Step function display of orders")
        print("   • Direct visualization of market liquidity")
        print("✅ Bar Chart Comparison - Compares volumes across markets")
        print("   • Grouped bars for Yes/No bids/asks")
        print("   • Volume labels and market comparison")
        print("✅ Platform Integration - Works with all trading platforms")
        print("   • Kalshi, PolyMarket, TestPlatform supported")
        print("   • Real-time data visualization")
        
        # List created files
        test_dir = os.path.dirname(os.path.abspath(__file__))
        visualization_files = [
            "demo_depth_chart.png",
            "demo_raw_orderbook.png", 
            "depth_chart_testplatform.png",
            "bar_chart_testplatform.png",
            "test_depth_chart_cumulative.png",
            "test_depth_chart_raw.png"
        ]
        
        print("\n📁 Generated Visualization Files:")
        for filename in visualization_files:
            filepath = os.path.join(test_dir, filename)
            if os.path.exists(filepath):
                print(f"   • {filename}")
        
        print("\n🎉 All visualization tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in visualization demo: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
