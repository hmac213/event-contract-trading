#!/bin/bash

# Reset System Script for Event Contract Trading
# Provides clean slate for development and testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REDIS_ONLY=false
DB_ONLY=false
MOCK_ONLY=false
ALL=false
HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --redis)
      REDIS_ONLY=true
      shift
      ;;
    --db)
      DB_ONLY=true
      shift
      ;;
    --mock)
      MOCK_ONLY=true
      shift
      ;;
    --all)
      ALL=true
      shift
      ;;
    --help|-h)
      HELP=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Help function
show_help() {
    echo -e "${BLUE}Event Contract Trading - System Reset Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --redis     Clear Redis streams and data only"
    echo "  --db        Clear database tables only (real tables)"
    echo "  --mock      Clear mock trading tables only"
    echo "  --all       Clear everything (Redis + DB + Mock)"
    echo "  --help, -h  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --redis              # Clear only Redis"
    echo "  $0 --db                 # Clear only real database tables"
    echo "  $0 --mock               # Clear only mock trading data"
    echo "  $0 --all                # Nuclear option - clear everything"
    echo "  $0 --redis --mock       # Clear Redis and mock data"
    echo ""
}

# Redis reset function
reset_redis() {
    echo -e "${YELLOW}🔄 Resetting Redis...${NC}"
    
    # Check if Redis container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "event-contract-trading-redis-1"; then
        echo -e "${YELLOW}📡 Starting Redis container...${NC}"
        docker-compose up redis -d
        sleep 2
    fi
    
    echo -e "${BLUE}🗑️  Flushing all Redis data...${NC}"
    docker exec event-contract-trading-redis-1 redis-cli FLUSHALL
    
    echo -e "${BLUE}📊 Recreating consumer groups...${NC}"
    # We'll recreate these when services start up
    
    echo -e "${GREEN}✅ Redis reset complete${NC}"
}

# Database reset function  
reset_database() {
    echo -e "${YELLOW}🔄 Resetting database tables...${NC}"
    
    # Check if we have database connection info
    if [[ -z "$SUPABASE_URL" || -z "$SUPABASE_KEY" ]]; then
        if [[ -f ".env" ]]; then
            echo -e "${BLUE}📁 Loading environment variables from .env...${NC}"
            set -a  # Export all variables
            source .env
            set +a  # Stop exporting
        else
            echo -e "${RED}❌ No .env file found and no database credentials in environment${NC}"
            echo -e "${YELLOW}💡 Please ensure SUPABASE_URL and SUPABASE_KEY are set${NC}"
            return 1
        fi
    fi
    
    echo -e "${BLUE}🗑️  Clearing real trading tables...${NC}"
    
    # Use Python to clear database tables (activate venv if it exists)
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    PYTHONPATH=. python3 -c "
import os
import sys
sys.path.append('.')
from db.DBManager import DBManager

try:
    db = DBManager()
    
    # Clear tables in order (respecting foreign key constraints)
    tables_to_clear = [
        'trades',
        'orders', 
        'orderbooks',
        'market_pairs',
        'markets'
    ]
    
    for table in tables_to_clear:
        try:
            result = db.supabase.table(table).delete().neq('id', -1).execute()
            print(f'✅ Cleared {table} table')
        except Exception as e:
            print(f'⚠️  Warning clearing {table}: {e}')
    
    print('✅ Database reset complete')
    
except Exception as e:
    print(f'❌ Database reset failed: {e}')
    exit(1)
"
    
    echo -e "${GREEN}✅ Database reset complete${NC}"
}

# Mock database reset function
reset_mock_database() {
    echo -e "${YELLOW}🔄 Resetting mock trading tables...${NC}"
    
    # Check if we have database connection info
    if [[ -z "$SUPABASE_URL" || -z "$SUPABASE_KEY" ]]; then
        if [[ -f ".env" ]]; then
            echo -e "${BLUE}📁 Loading environment variables from .env...${NC}"
            set -a  # Export all variables
            source .env
            set +a  # Stop exporting
        else
            echo -e "${RED}❌ No .env file found and no database credentials in environment${NC}"
            echo -e "${YELLOW}💡 Please ensure SUPABASE_URL and SUPABASE_KEY are set${NC}"
            return 1
        fi
    fi
    
    echo -e "${BLUE}🎭 Clearing mock trading tables...${NC}"
    
    # Use Python to clear mock database tables (activate venv if it exists)
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    PYTHONPATH=. python3 -c "
import os
import sys
sys.path.append('.')
from services.mock_trade_executor.mock_db_manager import MockDBManager

try:
    mock_db = MockDBManager()
    
    # Reset all mock data
    mock_db.reset_mock_data()
    print('✅ Mock database reset complete')
    
    # Reinitialize balances
    mock_db.initialize_mock_balances()
    print('💰 Mock balances reinitialized to \$50,000 per platform')
    
except Exception as e:
    print(f'❌ Mock database reset failed: {e}')
    exit(1)
"
    
    echo -e "${GREEN}✅ Mock database reset complete${NC}"
}

# Main execution
main() {
    if [[ "$HELP" == true ]]; then
        show_help
        exit 0
    fi
    
    # If no specific options, default to showing help
    if [[ "$REDIS_ONLY" == false && "$DB_ONLY" == false && "$MOCK_ONLY" == false && "$ALL" == false ]]; then
        echo -e "${YELLOW}⚠️  No reset options specified${NC}"
        show_help
        exit 1
    fi
    
    echo -e "${BLUE}🚀 Event Contract Trading - System Reset${NC}"
    echo -e "${YELLOW}⚠️  This will permanently delete data. Continue? (y/N)${NC}"
    read -r confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🛑 Reset cancelled${NC}"
        exit 0
    fi
    
    echo ""
    
    # Execute resets based on flags
    if [[ "$ALL" == true ]]; then
        reset_redis
        echo ""
        reset_database  
        echo ""
        reset_mock_database
    else
        if [[ "$REDIS_ONLY" == true ]]; then
            reset_redis
            echo ""
        fi
        
        if [[ "$DB_ONLY" == true ]]; then
            reset_database
            echo ""
        fi
        
        if [[ "$MOCK_ONLY" == true ]]; then
            reset_mock_database
            echo ""
        fi
    fi
    
    echo -e "${GREEN}🎉 System reset complete!${NC}"
    echo -e "${BLUE}💡 You can now start your services with: docker-compose --profile data --profile mock-trading up${NC}"
}

# Run main function
main "$@"
