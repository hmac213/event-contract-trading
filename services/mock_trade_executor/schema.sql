-- Mock Trading Database Schema
-- These tables mirror the real trading tables but are separate to avoid interference

-- Mock balances table - tracks mock account balances for each platform
CREATE TABLE IF NOT EXISTS mock_balances (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL UNIQUE,
    balance BIGINT NOT NULL DEFAULT 0, -- Balance in cents
    initial_balance BIGINT NOT NULL DEFAULT 0, -- Starting balance for P&L calculations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mock orders table - mirrors the real orders table structure
CREATE TABLE IF NOT EXISTS mock_orders (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'yes' or 'no'
    action VARCHAR(10) NOT NULL, -- 'buy' or 'sell'
    order_type VARCHAR(20) NOT NULL, -- 'market' or 'limit'
    quantity INTEGER NOT NULL,
    limit_price INTEGER, -- Price in cents (for limit orders)
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    client_order_id VARCHAR(255) UNIQUE,
    platform_order_id VARCHAR(255), -- Mock platform-specific order ID
    fill_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mock trades table - mirrors the real trades table structure
CREATE TABLE IF NOT EXISTS mock_trades (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES mock_orders(id),
    platform_trade_id VARCHAR(255), -- Mock platform-specific trade ID
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL, -- Price in cents
    executed_at INTEGER NOT NULL, -- Unix timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_mock_orders_status ON mock_orders(status);
CREATE INDEX IF NOT EXISTS idx_mock_orders_platform ON mock_orders(platform);
CREATE INDEX IF NOT EXISTS idx_mock_orders_market_id ON mock_orders(market_id);
CREATE INDEX IF NOT EXISTS idx_mock_trades_order_id ON mock_trades(order_id);
CREATE INDEX IF NOT EXISTS idx_mock_trades_executed_at ON mock_trades(executed_at);

-- Add constraints
ALTER TABLE mock_balances 
ADD CONSTRAINT check_platform_valid 
CHECK (platform IN ('kalshi', 'polymarket'));

ALTER TABLE mock_orders 
ADD CONSTRAINT check_side_valid 
CHECK (side IN ('yes', 'no'));

ALTER TABLE mock_orders 
ADD CONSTRAINT check_action_valid 
CHECK (action IN ('buy', 'sell'));

ALTER TABLE mock_orders 
ADD CONSTRAINT check_order_type_valid 
CHECK (order_type IN ('market', 'limit'));

ALTER TABLE mock_orders 
ADD CONSTRAINT check_status_valid 
CHECK (status IN ('pending', 'open', 'executed', 'canceled', 'failed', 'partially_filled'));

-- Comments for documentation
COMMENT ON TABLE mock_balances IS 'Mock account balances for testing trading strategies';
COMMENT ON TABLE mock_orders IS 'Mock orders that simulate real trading orders';
COMMENT ON TABLE mock_trades IS 'Mock trade executions for testing purposes';

COMMENT ON COLUMN mock_balances.balance IS 'Current balance in cents';
COMMENT ON COLUMN mock_balances.initial_balance IS 'Starting balance for P&L calculations';
COMMENT ON COLUMN mock_orders.quantity IS 'Number of shares to buy/sell';
COMMENT ON COLUMN mock_orders.limit_price IS 'Price per share in cents';
COMMENT ON COLUMN mock_trades.price IS 'Execution price per share in cents';
