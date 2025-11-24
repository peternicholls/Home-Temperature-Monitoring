#!/usr/bin/env bash
# Interactive report scaffolding and guidance
# Creates implementation report from template with proper naming and frontmatter

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths
eval $(get_feature_paths)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 IMPLEMENTATION REPORT SCAFFOLDING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Current Feature: $CURRENT_BRANCH"
echo "Feature Directory: $FEATURE_DIR"
echo ""

# Extract feature number from branch/directory name
FEATURE_NUM=$(echo "$CURRENT_BRANCH" | grep -o '^[0-9]*' || basename "$FEATURE_DIR" | grep -o '^[0-9]*')
if [[ -z "$FEATURE_NUM" ]]; then
    echo "❌ ERROR: Cannot determine feature number from branch/directory" >&2
    echo "   Branch: $CURRENT_BRANCH" >&2
    echo "   Directory: $FEATURE_DIR" >&2
    exit 1
fi

# Prompt for report details
echo "Report Details:"
echo "━━━━━━━━━━━━━━"
echo ""

read -p "Phase number (e.g., 1, 2, 3): " PHASE
if [[ -z "$PHASE" ]]; then
    echo "❌ ERROR: Phase number required" >&2
    exit 1
fi

read -p "Brief description (e.g., health-check, retry-logic, log-rotation): " DESCRIPTION
if [[ -z "$DESCRIPTION" ]]; then
    echo "❌ ERROR: Description required" >&2
    exit 1
fi

read -p "User story (e.g., US1, US2, US3): " USER_STORY
if [[ -z "$USER_STORY" ]]; then
    echo "❌ ERROR: User story required" >&2
    exit 1
fi

# Extract sprint name from current branch/directory
SPRINT_NAME=$(basename "$FEATURE_DIR" | sed 's/^[0-9]*-//')
if [[ -z "$SPRINT_NAME" ]]; then
    SPRINT_NAME="$CURRENT_BRANCH"
fi

# Generate filename with proper format: YYYY-MM-DD-spec-NNN-phase-N-description-implementation-report.md
DATE=$(date +%Y-%m-%d)
FILENAME="${DATE}-spec-${FEATURE_NUM}-phase-${PHASE}-${DESCRIPTION}-implementation-report.md"
REPORT_PATH="$REPO_ROOT/docs/reports/$FILENAME"

# Check if report already exists
if [[ -f "$REPORT_PATH" ]]; then
    echo ""
    echo "⚠️  Warning: Report already exists: $FILENAME"
    read -p "Overwrite existing report? (y/N): " OVERWRITE
    if [[ "$OVERWRITE" != "y" && "$OVERWRITE" != "Y" ]]; then
        echo "❌ Aborted - report not created"
        exit 1
    fi
fi

# Verify template exists
TEMPLATE_PATH="$REPO_ROOT/.specify/templates/report-template.md"
if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "❌ ERROR: Report template not found: $TEMPLATE_PATH" >&2
    exit 1
fi

# Create reports directory if it doesn't exist
mkdir -p "$REPO_ROOT/docs/reports"

# Create report from template
cp "$TEMPLATE_PATH" "$REPORT_PATH"

# Populate frontmatter and placeholders
# Note: Using portable sed syntax (works on both macOS and Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS sed requires -i ''
    sed -i '' "s/\[NNN\]/${FEATURE_NUM}/g" "$REPORT_PATH"
    sed -i '' "s/\[N\]/${PHASE}/g" "$REPORT_PATH"
    sed -i '' "s/\[USN\]/${USER_STORY}/g" "$REPORT_PATH"
    sed -i '' "s/\[YYYY-MM-DD\]/${DATE}/g" "$REPORT_PATH"
    sed -i '' "s/\[NNN-sprint-name\]/${FEATURE_NUM}-${SPRINT_NAME}/g" "$REPORT_PATH"
    sed -i '' "s/\[Sprint Name\]/${SPRINT_NAME}/g" "$REPORT_PATH"
else
    # Linux sed
    sed -i "s/\[NNN\]/${FEATURE_NUM}/g" "$REPORT_PATH"
    sed -i "s/\[N\]/${PHASE}/g" "$REPORT_PATH"
    sed -i "s/\[USN\]/${USER_STORY}/g" "$REPORT_PATH"
    sed -i "s/\[YYYY-MM-DD\]/${DATE}/g" "$REPORT_PATH"
    sed -i "s/\[NNN-sprint-name\]/${FEATURE_NUM}-${SPRINT_NAME}/g" "$REPORT_PATH"
    sed -i "s/\[Sprint Name\]/${SPRINT_NAME}/g" "$REPORT_PATH"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Report Created Successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📄 Report: $FILENAME"
echo "📂 Location: $REPORT_PATH"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 NEXT STEPS (from report-writing-process.md)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 📝 Fill Executive Summary (2-3 sentences)"
echo "   → What was implemented and its current state"
echo ""
echo "2. ✅ Document Key Achievements"
echo "   → Use ✅/⚠️/❌ indicators for each accomplishment"
echo "   → Be specific and measurable"
echo ""
echo "3. 🧪 Complete Implementation Details"
echo "   → Test suite: Total lines, test classes, scenarios, pass rate"
echo "   → Components: What was created/modified, file sizes, functionality"
echo "   → Supporting infrastructure: Config changes, helper functions, etc."
echo ""
echo "4. 📊 Report Test Results"
echo "   → Include pytest command output"
echo "   → Show pass/fail rates and coverage percentages"
echo "   → Document execution times"
echo ""
echo "5. 🔬 Document Technical Decisions (3-5 minimum)"
echo "   → What was decided, why, and what impact it had"
echo "   → Include alternatives considered"
echo ""
echo "6. 📖 Write Lessons Learned"
echo "   → This is CRITICAL - will be categorized into central knowledge base"
echo "   → Include 3-7 detailed, actionable lessons"
echo "   → Be specific with examples and technical details"
echo "   → Format: Numbered list with **Title**: Description"
echo ""
echo "7. 📏 Fill Code Metrics"
echo "   → Files modified/created, lines added, test coverage"
echo ""
echo "8. ✍️  Complete Sign-Off Section"
echo "   → Update status indicators (✅/⚠️/❌)"
echo "   → Final assessment and deployment clearance"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 REFERENCE DOCUMENTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• Report Writing Process: .specify/templates/commands/report-writing-process.md"
echo "• Report Template: $TEMPLATE_PATH"
echo "• Example Reports: docs/reports/2024-11-21-spec-005-phase-*.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 TIP: After completing the report:"
echo "   1. Validate completeness:"
echo "      → .specify/scripts/bash/validate-report.sh $REPORT_PATH"
echo ""
echo "   2. Extract lessons to knowledge base:"
echo "      → .specify/scripts/bash/extract-lessons-learned.sh"
echo "      → Review extracted lessons"
echo "      → Manually categorize into .specify/memory/lessons-learned.md"
echo ""
