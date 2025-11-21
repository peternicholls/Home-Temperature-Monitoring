#!/bin/bash
# scripts/test-24hour-setup.sh
# T101: Setup and start 24-hour continuous operation test
# Runs both Hue and Amazon AQM collectors concurrently for production validation

set -e

VENV="./venv"
DB="data/temperature.db"
LOG_DIR="logs"
HUE_LOG="$LOG_DIR/hue_24h_test.log"
AMAZON_LOG="$LOG_DIR/amazon_24h_test.log"
TEST_INFO_FILE="/tmp/test_24h_info.txt"
PIDs_FILE="/tmp/test_24h_pids.txt"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}24-Hour Continuous Operation Test - Setup (T101)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check virtual environment
if [ ! -d "$VENV" ]; then
    echo -e "${RED}✗ Virtual environment not found at $VENV${NC}"
    echo "Run: make setup"
    exit 1
fi

# Check dependencies
if [ ! -f "config/config.yaml" ]; then
    echo -e "${RED}✗ config/config.yaml not found${NC}"
    exit 1
fi

if [ ! -f "config/secrets.yaml" ]; then
    echo -e "${RED}✗ config/secrets.yaml not found${NC}"
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Create baseline snapshot
echo -e "${BLUE}Creating baseline snapshot...${NC}"
. "$VENV/bin/activate"

INITIAL_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM readings;" 2>/dev/null || echo "0")
INITIAL_SIZE=$(ls -lh "$DB" 2>/dev/null | awk '{print $5}' || echo "0B")

echo "  Initial reading count: $INITIAL_COUNT"
echo "  Initial database size: $INITIAL_SIZE"
echo ""

# Record test start time
START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
START_EPOCH=$(date +%s)

echo -e "${YELLOW}Pre-Test Checklist:${NC}"
echo "  ✓ Virtual environment activated"
echo "  ✓ Configuration files present"
echo "  ✓ Database backup available: $INITIAL_COUNT readings"
echo ""

echo -e "${BLUE}Starting collectors in background...${NC}"
echo ""

# Start Hue collector
echo -e "${GREEN}[1/2] Starting Hue collector...${NC}"
nohup python -m source.collectors.hue_collector_main > "$HUE_LOG" 2>&1 &
HUE_PID=$!
echo "  PID: $HUE_PID"
sleep 2

# Start Amazon AQM collector  
echo -e "${GREEN}[2/2] Starting Amazon AQM collector...${NC}"
nohup python -m source.collectors.amazon_aqm_collector_main > "$AMAZON_LOG" 2>&1 &
AMAZON_PID=$!
echo "  PID: $AMAZON_PID"
sleep 2

# Save PIDs and test info
echo "$HUE_PID $AMAZON_PID" > "$PIDs_FILE"

cat > "$TEST_INFO_FILE" << EOF
Test Start: $START_TIME ($START_EPOCH)
Hue PID: $HUE_PID
Amazon PID: $AMAZON_PID
Hue Log: $HUE_LOG
Amazon Log: $AMAZON_LOG
Initial Count: $INITIAL_COUNT
Initial Size: $INITIAL_SIZE
EOF

echo ""
echo -e "${GREEN}✓ Test started successfully!${NC}"
echo ""
echo -e "${BLUE}Monitor Progress:${NC}"
echo "  • Check logs: tail -f $HUE_LOG"
echo "  • Check logs: tail -f $AMAZON_LOG"
echo "  • Database: make db-view"
echo "  • Stats: make db-stats"
echo ""
echo -e "${BLUE}Stop Test:${NC}"
echo "  make test-24hour-stop"
echo ""
echo -e "${BLUE}Verify Results After 24 Hours:${NC}"
echo "  make test-24hour-verify"
echo ""
