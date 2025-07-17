
import matplotlib.pyplot as plt
import numpy as np

def plot_depth_chart(order_book, platform_name, market_name):
    """
    Plot depth chart for order book data similar to the reference images
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'{market_name}\nDepth Chart - {platform_name}', fontsize=14, fontweight='bold')
    
    # Helper function to calculate cumulative depth
    def calculate_cumulative_depth(orders):
        if not orders:
            return [], []
        
        prices = [order[0] for order in orders]
        quantities = [order[1] for order in orders]
        
        # Sort by price
        sorted_data = sorted(zip(prices, quantities))
        prices_sorted = [x[0] for x in sorted_data]
        quantities_sorted = [x[1] for x in sorted_data]
        
        # Calculate cumulative quantities
        cumulative_quantities = np.cumsum(quantities_sorted)
        
        return prices_sorted, cumulative_quantities
    
    # Plot Yes Bids and Asks
    if 'bid' in order_book.yes and 'ask' in order_book.yes:
        yes_bid_prices, yes_bid_cumulative = calculate_cumulative_depth(order_book.yes['bid'])
        yes_ask_prices, yes_ask_cumulative = calculate_cumulative_depth(order_book.yes['ask'])
        
        # Convert prices to percentages (prices are already in format like 10, 20, 30 = 1%, 2%, 3%)
        yes_bid_prices_pct = [p / 10 for p in yes_bid_prices]
        yes_ask_prices_pct = [p / 10 for p in yes_ask_prices]
        
        # Plot Yes market
        ax1.set_title('Yes', fontweight='bold')
        if yes_bid_prices_pct and len(yes_bid_cumulative) > 0:
            ax1.step(yes_bid_prices_pct, yes_bid_cumulative, where='post', 
                    color='green', linewidth=2, label='Yes Bids (Cumulative)', alpha=0.7)
            ax1.fill_between(yes_bid_prices_pct, yes_bid_cumulative, 
                           step='post', color='green', alpha=0.3)
        
        if yes_ask_prices_pct and len(yes_ask_cumulative) > 0:
            ax1.step(yes_ask_prices_pct, yes_ask_cumulative, where='post', 
                    color='red', linewidth=2, label='Yes Asks (Cumulative)', alpha=0.7)
            ax1.fill_between(yes_ask_prices_pct, yes_ask_cumulative, 
                           step='post', color='red', alpha=0.3)
        
        ax1.set_xlabel('Price (Probability %)')
        ax1.set_ylabel('Cumulative Quantity')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 100)
    
    # Plot No Bids and Asks  
    if 'bid' in order_book.no and 'ask' in order_book.no:
        no_bid_prices, no_bid_cumulative = calculate_cumulative_depth(order_book.no['bid'])
        no_ask_prices, no_ask_cumulative = calculate_cumulative_depth(order_book.no['ask'])
        
        # Convert prices to percentages
        no_bid_prices_pct = [p / 10 for p in no_bid_prices]
        no_ask_prices_pct = [p / 10 for p in no_ask_prices]
        
        # Plot No market
        ax2.set_title('No', fontweight='bold')
        if no_bid_prices_pct and len(no_bid_cumulative) > 0:
            ax2.step(no_bid_prices_pct, no_bid_cumulative, where='post', 
                    color='green', linewidth=2, label='No Bids (Cumulative)', alpha=0.7)
            ax2.fill_between(no_bid_prices_pct, no_bid_cumulative, 
                           step='post', color='green', alpha=0.3)
        
        if no_ask_prices_pct and len(no_ask_cumulative) > 0:
            ax2.step(no_ask_prices_pct, no_ask_cumulative, where='post', 
                    color='red', linewidth=2, label='No Asks (Cumulative)', alpha=0.7)
            ax2.fill_between(no_ask_prices_pct, no_ask_cumulative, 
                           step='post', color='red', alpha=0.3)
        
        ax2.set_xlabel('Price (Probability %)')
        ax2.set_ylabel('Cumulative Quantity')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 100)
    
    # Raw order book visualization (bottom plots)
    ax3.set_title('Yes - Raw Orders', fontweight='bold')
    if 'bid' in order_book.yes and order_book.yes['bid']:
        yes_bid_prices_raw = [order[0] / 10 for order in order_book.yes['bid']]
        yes_bid_quantities_raw = [order[1] / 1000 for order in order_book.yes['bid']]  # Scale down for visibility
        ax3.bar(yes_bid_prices_raw, yes_bid_quantities_raw, color='green', alpha=0.7, width=1, label='Yes Bids')
    
    if 'ask' in order_book.yes and order_book.yes['ask']:
        yes_ask_prices_raw = [order[0] / 10 for order in order_book.yes['ask']]
        yes_ask_quantities_raw = [order[1] / 1000 for order in order_book.yes['ask']]  # Scale down for visibility
        ax3.bar(yes_ask_prices_raw, yes_ask_quantities_raw, color='red', alpha=0.7, width=1, label='Yes Asks')
    
    ax3.set_xlabel('Price (Probability %)')
    ax3.set_ylabel('Quantity (thousands)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 100)
    
    ax4.set_title('No - Raw Orders', fontweight='bold')
    if 'bid' in order_book.no and order_book.no['bid']:
        no_bid_prices_raw = [order[0] / 10 for order in order_book.no['bid']]
        no_bid_quantities_raw = [order[1] / 1000 for order in order_book.no['bid']]  # Scale down for visibility
        ax4.bar(no_bid_prices_raw, no_bid_quantities_raw, color='green', alpha=0.7, width=1, label='No Bids')
    
    if 'ask' in order_book.no and order_book.no['ask']:
        no_ask_prices_raw = [order[0] / 10 for order in order_book.no['ask']]
        no_ask_quantities_raw = [order[1] / 1000 for order in order_book.no['ask']]  # Scale down for visibility
        ax4.bar(no_ask_prices_raw, no_ask_quantities_raw, color='red', alpha=0.7, width=1, label='No Asks')
    
    ax4.set_xlabel('Price (Probability %)')
    ax4.set_ylabel('Quantity (thousands)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 100)
    
    plt.tight_layout()
    return fig