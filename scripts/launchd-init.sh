#!/bin/bash
# scripts/launchd-init.sh
# Initialize launchd agents for scheduled collection
# Creates plist files in ~/.config/LaunchAgents/

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Initializing launchd Collection Agents${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Get absolute paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
LOGS_DIR="$PROJECT_ROOT/logs"
LAUNCHAGENTS_DIR="$HOME/.config/LaunchAgents"

# Create LaunchAgents directory if it doesn't exist
if [ ! -d "$LAUNCHAGENTS_DIR" ]; then
    echo -e "${YELLOW}Creating directory: $LAUNCHAGENTS_DIR${NC}"
    mkdir -p "$LAUNCHAGENTS_DIR"
fi

# Create logs directory
mkdir -p "$LOGS_DIR"

echo -e "${BLUE}Configuration:${NC}"
echo "  Project Root: $PROJECT_ROOT"
echo "  Scripts Dir: $SCRIPTS_DIR"
echo "  Logs Dir: $LOGS_DIR"
echo "  LaunchAgents Dir: $LAUNCHAGENTS_DIR"
echo ""

# Hue agent plist
HUE_PLIST="$LAUNCHAGENTS_DIR/com.hometemperaturemonitoring.hue.plist"
echo -e "${BLUE}Creating Hue collector agent...${NC}"

cat > "$HUE_PLIST" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hometemperaturemonitoring.hue</string>
    
    <key>Program</key>
    <string>HUE_SCRIPT_PATH</string>
    
    <key>StartInterval</key>
    <integer>300</integer>
    
    <key>StandardOutPath</key>
    <string>HUE_LOG_PATH</string>
    
    <key>StandardErrorPath</key>
    <string>HUE_LOG_PATH</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
PLIST_EOF

# Replace placeholders in Hue plist
sed -i '' "s|HUE_SCRIPT_PATH|$SCRIPTS_DIR/collectors-hue-runner.sh|g" "$HUE_PLIST"
sed -i '' "s|HUE_LOG_PATH|$LOGS_DIR/hue_scheduled.log|g" "$HUE_PLIST"

echo "  ✓ Created: $HUE_PLIST"

# Amazon agent plist
AMAZON_PLIST="$LAUNCHAGENTS_DIR/com.hometemperaturemonitoring.amazon.plist"
echo -e "${BLUE}Creating Amazon AQM collector agent...${NC}"

cat > "$AMAZON_PLIST" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hometemperaturemonitoring.amazon</string>
    
    <key>Program</key>
    <string>AMAZON_SCRIPT_PATH</string>
    
    <key>StartInterval</key>
    <integer>300</integer>
    
    <key>StandardOutPath</key>
    <string>AMAZON_LOG_PATH</string>
    
    <key>StandardErrorPath</key>
    <string>AMAZON_LOG_PATH</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
PLIST_EOF

# Replace placeholders in Amazon plist
sed -i '' "s|AMAZON_SCRIPT_PATH|$SCRIPTS_DIR/collectors-amazon-runner.sh|g" "$AMAZON_PLIST"
sed -i '' "s|AMAZON_LOG_PATH|$LOGS_DIR/amazon_scheduled.log|g" "$AMAZON_PLIST"

echo "  ✓ Created: $AMAZON_PLIST"

# Make scripts executable
echo ""
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x "$SCRIPTS_DIR/collectors-hue-runner.sh"
chmod +x "$SCRIPTS_DIR/collectors-amazon-runner.sh"
echo "  ✓ Scripts are executable"

echo ""
echo -e "${GREEN}✓ Initialization complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Load services: make collection-start"
echo "  2. Check status: make collection-status"
echo "  3. View logs: make collection-logs"
echo ""
