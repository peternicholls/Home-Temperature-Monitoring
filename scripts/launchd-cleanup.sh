#!/bin/bash
# scripts/launchd-cleanup.sh
# Unload and remove launchd agents

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Cleaning up launchd Collection Agents${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

LAUNCHAGENTS_DIR="$HOME/.config/LaunchAgents"
HUE_PLIST="$LAUNCHAGENTS_DIR/com.hometemperaturemonitoring.hue.plist"
AMAZON_PLIST="$LAUNCHAGENTS_DIR/com.hometemperaturemonitoring.amazon.plist"

# Unload Hue agent
echo -e "${BLUE}Unloading Hue collector agent...${NC}"
if [ -f "$HUE_PLIST" ]; then
    launchctl unload "$HUE_PLIST" 2>/dev/null || echo "  (Agent not loaded or already unloaded)"
    rm -f "$HUE_PLIST"
    echo "  ✓ Removed: $HUE_PLIST"
else
    echo "  (Not found)"
fi

# Unload Amazon agent
echo -e "${BLUE}Unloading Amazon AQM collector agent...${NC}"
if [ -f "$AMAZON_PLIST" ]; then
    launchctl unload "$AMAZON_PLIST" 2>/dev/null || echo "  (Agent not loaded or already unloaded)"
    rm -f "$AMAZON_PLIST"
    echo "  ✓ Removed: $AMAZON_PLIST"
else
    echo "  (Not found)"
fi

echo ""
echo -e "${GREEN}✓ Cleanup complete!${NC}"
echo ""
