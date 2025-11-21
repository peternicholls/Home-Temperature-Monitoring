#!/bin/bash
# scripts/test-24hour-stop.sh
# Stop the 24-hour continuous operation test gracefully

set -e

PIDs_FILE="/tmp/test_24h_pids.txt"
TEST_INFO_FILE="/tmp/test_24h_info.txt"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}24-Hour Test - Stopping Collectors${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -f "$PIDs_FILE" ]; then
    echo -e "${RED}✗ No test running (PID file not found)${NC}"
    exit 1
fi

read HUE_PID AMAZON_PID < "$PIDs_FILE"

echo -e "${BLUE}Stopping collectors gracefully...${NC}"

if kill -0 "$HUE_PID" 2>/dev/null; then
    echo -e "${YELLOW}Stopping Hue collector (PID: $HUE_PID)...${NC}"
    kill "$HUE_PID"
    sleep 3
    if kill -0 "$HUE_PID" 2>/dev/null; then
        echo -e "${RED}Force killing Hue collector...${NC}"
        kill -9 "$HUE_PID"
    fi
    echo -e "${GREEN}✓ Hue collector stopped${NC}"
else
    echo -e "${YELLOW}Hue collector already stopped${NC}"
fi

if kill -0 "$AMAZON_PID" 2>/dev/null; then
    echo -e "${YELLOW}Stopping Amazon AQM collector (PID: $AMAZON_PID)...${NC}"
    kill "$AMAZON_PID"
    sleep 3
    if kill -0 "$AMAZON_PID" 2>/dev/null; then
        echo -e "${RED}Force killing Amazon collector...${NC}"
        kill -9 "$AMAZON_PID"
    fi
    echo -e "${GREEN}✓ Amazon AQM collector stopped${NC}"
else
    echo -e "${YELLOW}Amazon AQM collector already stopped${NC}"
fi

echo ""
echo -e "${GREEN}✓ All collectors stopped${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  make test-24hour-verify"
echo ""

# Keep test info file for verification
