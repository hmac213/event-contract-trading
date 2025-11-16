#!/bin/bash

# Startup Monitor Script for Event Contract Trading
# Monitors the startup coordination and service status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Event Contract Trading - Startup Monitor${NC}"
echo ""

# Function to check if Redis container is running
check_redis() {
    if docker ps --format "table {{.Names}}" | grep -q "event-contract-trading-redis-1"; then
        echo -e "${GREEN}✅ Redis container is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Redis container is not running${NC}"
        return 1
    fi
}

# Function to get startup coordination status
get_startup_status() {
    if ! check_redis; then
        return 1
    fi
    
    echo -e "${CYAN}📊 Startup Coordination Status:${NC}"
    echo "=========================================="
    
    # Use Python to get detailed startup status
    python3 -c "
import sys
import json
sys.path.append('.')
try:
    from utils.startup_coordinator import StartupCoordinator
    coordinator = StartupCoordinator()
    status = coordinator.get_startup_status()
    
    services = status.get('services', {})
    if not services:
        print('🔍 No services have reported startup status yet')
        sys.exit(0)
    
    for service_name, attributes in services.items():
        phase = attributes.get('phase', 'unknown')
        ready_time = attributes.get('ready')
        initial_load = attributes.get('initial_load_complete')
        
        print(f'📦 {service_name}:')
        print(f'  └─ Phase: {phase}')
        
        if ready_time:
            print(f'  └─ Ready: ✅ (at {ready_time})')
        else:
            print(f'  └─ Ready: ⏳ Waiting...')
            
        if initial_load:
            markets_loaded, timestamp = initial_load.split(':')
            print(f'  └─ Initial Load: ✅ {markets_loaded} markets loaded')
        else:
            print(f'  └─ Initial Load: ⏳ Waiting...')
        print()
    
except Exception as e:
    print(f'❌ Error getting startup status: {e}')
    sys.exit(1)
"
}

# Function to monitor container logs
monitor_logs() {
    echo -e "${CYAN}📋 Recent Container Logs:${NC}"
    echo "=========================================="
    
    services=("market_poller" "market_similarity" "arbitrage_finder" "mock_trade_executor")
    
    for service in "${services[@]}"; do
        container_name="event-contract-trading-${service}-1"
        if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
            echo -e "${GREEN}📦 $service (last 3 lines):${NC}"
            docker logs "$container_name" --tail=3 2>/dev/null || echo "  No logs available"
            echo ""
        else
            echo -e "${YELLOW}📦 $service: Container not running${NC}"
        fi
    done
}

# Function to show Redis stream info
show_stream_info() {
    if ! check_redis; then
        return 1
    fi
    
    echo -e "${CYAN}🌊 Redis Stream Information:${NC}"
    echo "=========================================="
    
    streams=("market_events_stream" "similar_market_pairs_stream" "arbitrage_opportunities_stream")
    
    for stream in "${streams[@]}"; do
        length=$(docker exec event-contract-trading-redis-1 redis-cli XLEN "$stream" 2>/dev/null || echo "0")
        echo -e "${GREEN}📊 $stream:${NC} $length messages"
    done
    echo ""
}

# Main execution
main() {
    while true; do
        clear
        echo -e "${BLUE}🚀 Event Contract Trading - Startup Monitor${NC}"
        echo -e "${YELLOW}$(date)${NC}"
        echo ""
        
        get_startup_status
        echo ""
        
        show_stream_info
        echo ""
        
        monitor_logs
        
        echo -e "${YELLOW}⏰ Refreshing in 10 seconds... (Ctrl+C to exit)${NC}"
        sleep 10
    done
}

# Handle command line arguments
if [[ "$1" == "--once" ]]; then
    get_startup_status
    echo ""
    show_stream_info
    echo ""
    monitor_logs
else
    main
fi
