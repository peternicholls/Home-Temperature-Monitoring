#!/bin/bash
# .specify/scripts/bash/extract-lessons-learned.sh
# Extracts 'Lessons Learned' from latest implementation report
# Displays lessons for manual categorization into .specify/memory/lessons-learned.md

set -e

REPORTS_DIR="docs/reports"
LESSONS_FILE=".specify/memory/lessons-learned.md"
DATE=$(date +"%Y-%m-%d")

# Parse command line options
AUTO_APPEND=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --auto-append)
      AUTO_APPEND=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--auto-append]"
      exit 1
      ;;
  esac
done

# 1. Find the latest implementation report
latest_report=$(ls -t $REPORTS_DIR/*-implementation-report.md 2>/dev/null | head -n 1)
if [[ -z "$latest_report" ]]; then
  echo "❌ No implementation report found in $REPORTS_DIR."
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 LESSONS LEARNED EXTRACTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Report: $(basename "$latest_report")"
echo "Knowledge Base: $LESSONS_FILE"
echo ""

# 2. Extract 'Lessons Learned' section (stop at next header or horizontal rule)
lessons=$(awk '/^## Lessons Learned/{flag=1;next}/^## |^---/{flag=0}flag' "$latest_report")
if [[ -z "$lessons" ]]; then
  echo "❌ No 'Lessons Learned' section found in $latest_report."
  exit 1
fi

# 3. Check if lessons already exist in knowledge base
new_lessons=0
duplicate_lessons=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 EXTRACTED LESSONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "$lessons"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count lessons (numbered items)
lesson_count=$(echo "$lessons" | grep -c '^[0-9]\.' || echo "0")
echo ""
echo "✅ Found $lesson_count lessons in report"
echo ""

# 4. Check for potential duplicates by searching for key phrases
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 DUPLICATE CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while IFS= read -r line; do
  if [[ "$line" =~ ^[0-9]+\.\  ]]; then
    # Extract the lesson title (everything after "number. **" and before "**:")
    title=$(echo "$line" | sed -E 's/^[0-9]+\. \*\*(.+)\*\*:.*/\1/')
    if grep -q "$title" "$LESSONS_FILE" 2>/dev/null; then
      echo "⚠️  Already exists: $title"
      ((duplicate_lessons++))
    else
      echo "✨ New lesson: $title"
      ((new_lessons++))
    fi
  fi
done <<< "$lessons"

echo ""
echo "Summary: $new_lessons new, $duplicate_lessons already in knowledge base"
echo ""

if [[ $duplicate_lessons -gt 0 ]]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ LESSONS ALREADY INTEGRATED"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "All lessons from this report have been categorized in the knowledge base."
  echo "No further action needed."
  echo ""
  
  # Update last_updated timestamp
  if grep -q '^last_updated:' "$LESSONS_FILE"; then
    sed -i '' "s/^last_updated:.*/last_updated: \"$DATE\"/" "$LESSONS_FILE"
  fi
  
  exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Manual categorization recommended for best quality:"
echo ""
echo "1. Review extracted lessons above"
echo "2. Categorize each lesson into appropriate section:"
echo "   - Testing & Quality"
echo "   - Technical Architecture"
echo "   - Development Process"
echo "   - Performance & Optimization"
echo "   - Error Handling & Resilience"
echo "   - Tools & Frameworks"
echo "   - Security & Compliance"
echo "   - Sprint-Specific Insights"
echo ""
echo "3. Add source attribution (Sprint, Phase, Date)"
echo "4. Add actionable guidance for each lesson"
echo ""
echo "Or use --auto-append flag to append raw lessons (not recommended)"
echo ""
