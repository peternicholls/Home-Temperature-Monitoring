#!/usr/bin/env bash
# Verify report completeness before closing phase
# Checks for required sections and content quality

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Check if report path provided
REPORT_PATH="$1"

if [[ -z "$REPORT_PATH" ]]; then
    echo "Usage: $0 <report_path>" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  $0 docs/reports/2024-11-21-spec-005-phase-6-health-check-implementation-report.md" >&2
    echo "" >&2
    echo "Or validate latest report:" >&2
    echo "  $0 \$(ls -1t docs/reports/*.md | head -n 1)" >&2
    exit 1
fi

# Check if report exists
if [[ ! -f "$REPORT_PATH" ]]; then
    echo "❌ ERROR: Report not found: $REPORT_PATH" >&2
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 VALIDATING IMPLEMENTATION REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Report: $(basename "$REPORT_PATH")"
echo "Path: $REPORT_PATH"
echo ""

# Define required sections (these must exist in the report)
REQUIRED_SECTIONS=(
    "Executive Summary"
    "Key Achievements"
    "Implementation Details"
    "Test Results"
    "Technical Decisions"
    "Lessons Learned"
    "Code Metrics"
    "Sign-Off"
)

# Define warning sections (should exist but not critical)
WARNING_SECTIONS=(
    "Failure Analysis"
    "Verification Against Requirements"
    "Production Readiness Assessment"
)

# Track validation results
MISSING_SECTIONS=()
WARNING_MISSING=()
VALIDATION_ERRORS=()
VALIDATION_WARNINGS=()

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CHECKING REQUIRED SECTIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for required sections
for section in "${REQUIRED_SECTIONS[@]}"; do
    if grep -q "^## $section" "$REPORT_PATH"; then
        echo "✅ $section"
    else
        echo "❌ $section - MISSING"
        MISSING_SECTIONS+=("$section")
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  CHECKING RECOMMENDED SECTIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for warning sections
for section in "${WARNING_SECTIONS[@]}"; do
    if grep -q "^## $section" "$REPORT_PATH"; then
        echo "✅ $section"
    else
        echo "⚠️  $section - Not found (recommended for complete reports)"
        WARNING_MISSING+=("$section")
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 CHECKING CONTENT QUALITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check frontmatter
if ! grep -q "^---" "$REPORT_PATH" | head -n 1; then
    echo "❌ Frontmatter missing"
    VALIDATION_ERRORS+=("Frontmatter: YAML frontmatter not found at start of file")
else
    echo "✅ Frontmatter present"
    
    # Check frontmatter fields
    if ! grep -q "^sprint:" "$REPORT_PATH"; then
        echo "⚠️  Frontmatter: 'sprint' field missing"
        VALIDATION_WARNINGS+=("Frontmatter: 'sprint' field not found")
    fi
    
    if ! grep -q "^phase:" "$REPORT_PATH"; then
        echo "⚠️  Frontmatter: 'phase' field missing"
        VALIDATION_WARNINGS+=("Frontmatter: 'phase' field not found")
    fi
    
    if ! grep -q "^user_story:" "$REPORT_PATH"; then
        echo "⚠️  Frontmatter: 'user_story' field missing"
        VALIDATION_WARNINGS+=("Frontmatter: 'user_story' field not found")
    fi
fi

# Check for template placeholders that weren't filled (only common template patterns)
PLACEHOLDERS=$(grep -E '\[(NNN|USN|YYYY-MM-DD|Feature Name|Sprint Name|User Story Title|Task|N/N|N\])\]' "$REPORT_PATH" || true)
if [[ -n "$PLACEHOLDERS" ]]; then
    echo "❌ Unfilled placeholders found:"
    echo "$PLACEHOLDERS" | head -n 5
    PLACEHOLDER_COUNT=$(echo "$PLACEHOLDERS" | wc -l | tr -d ' ')
    VALIDATION_ERRORS+=("Unfilled placeholders: $PLACEHOLDER_COUNT placeholders need to be filled")
else
    echo "✅ No unfilled placeholders"
fi

# Check Lessons Learned section content (critical for extraction)
LESSONS_SECTION=$(sed -n '/^## Lessons Learned/,/^## /p' "$REPORT_PATH")
if [[ -n "$LESSONS_SECTION" ]]; then
    # Remove the last line (next section header) if present
    LESSONS_SECTION=$(echo "$LESSONS_SECTION" | sed '$d')
fi
LESSONS_LINES=$(echo "$LESSONS_SECTION" | wc -l | tr -d ' ')

if [[ $LESSONS_LINES -lt 20 ]]; then
    echo "❌ Lessons Learned section too short ($LESSONS_LINES lines)"
    VALIDATION_ERRORS+=("Lessons Learned: Section appears incomplete (<20 lines). Should have 3-7 detailed lessons.")
else
    echo "✅ Lessons Learned section has substantive content ($LESSONS_LINES lines)"
    
    # Count numbered lessons
    LESSON_COUNT=$(echo "$LESSONS_SECTION" | grep -c '^[0-9]\.' || echo "0")
    if [[ $LESSON_COUNT -lt 3 ]]; then
        echo "⚠️  Only $LESSON_COUNT lessons found (recommended: 3-7)"
        VALIDATION_WARNINGS+=("Lessons Learned: Only $LESSON_COUNT lessons found (recommended: 3-7)")
    else
        echo "✅ $LESSON_COUNT lessons documented"
    fi
fi

# Check Executive Summary
EXEC_SUMMARY=$(sed -n '/^## Executive Summary/,/^## /p' "$REPORT_PATH")
if [[ -n "$EXEC_SUMMARY" ]]; then
    # Remove the last line (next section header) if present
    EXEC_SUMMARY=$(echo "$EXEC_SUMMARY" | sed '$d')
fi
EXEC_SUMMARY_LINES=$(echo "$EXEC_SUMMARY" | grep -v '^#' | grep -v '^$' | wc -l | tr -d ' ')

if [[ $EXEC_SUMMARY_LINES -lt 3 ]]; then
    echo "⚠️  Executive Summary may be too brief ($EXEC_SUMMARY_LINES non-empty lines)"
    VALIDATION_WARNINGS+=("Executive Summary: Appears brief ($EXEC_SUMMARY_LINES lines). Should be 2-3 sentences.")
else
    echo "✅ Executive Summary has content ($EXEC_SUMMARY_LINES lines)"
fi

# Check for status indicators (✅/⚠️/❌)
STATUS_INDICATORS=$(grep -c '[✅⚠️❌]' "$REPORT_PATH" || echo "0")
if [[ $STATUS_INDICATORS -lt 5 ]]; then
    echo "⚠️  Few status indicators found ($STATUS_INDICATORS). Use ✅/⚠️/❌ for clarity"
    VALIDATION_WARNINGS+=("Status Indicators: Only $STATUS_INDICATORS found. Use more ✅/⚠️/❌ for visual clarity.")
else
    echo "✅ Status indicators used throughout ($STATUS_INDICATORS instances)"
fi

# Check Sign-Off section for final status
if grep -q "^## Sign-Off" "$REPORT_PATH"; then
    SIGNOFF_SECTION=$(sed -n '/^## Sign-Off/,/^## /p' "$REPORT_PATH")
    
    if ! echo "$SIGNOFF_SECTION" | grep -q "Status.*:"; then
        echo "⚠️  Sign-Off: Missing status declarations"
        VALIDATION_WARNINGS+=("Sign-Off: Missing status declarations (Phase Status, Production Ready, etc.)")
    else
        echo "✅ Sign-Off section has status declarations"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Report results
ERROR_COUNT=${#VALIDATION_ERRORS[@]}
MISSING_COUNT=${#MISSING_SECTIONS[@]}
WARNING_COUNT=$((${#VALIDATION_WARNINGS[@]} + ${#WARNING_MISSING[@]}))

echo "Required Sections: $((${#REQUIRED_SECTIONS[@]} - MISSING_COUNT))/${#REQUIRED_SECTIONS[@]} found"
echo "Critical Errors: $ERROR_COUNT"
echo "Warnings: $WARNING_COUNT"
echo ""

# Display errors if any
if [[ $MISSING_COUNT -gt 0 ]]; then
    echo "❌ Missing Required Sections:"
    printf '   - %s\n' "${MISSING_SECTIONS[@]}"
    echo ""
fi

if [[ $ERROR_COUNT -gt 0 ]]; then
    echo "❌ Critical Errors:"
    printf '   - %s\n' "${VALIDATION_ERRORS[@]}"
    echo ""
fi

# Display warnings if any
if [[ $WARNING_COUNT -gt 0 ]]; then
    echo "⚠️  Warnings:"
    if [[ ${#WARNING_MISSING[@]} -gt 0 ]]; then
        printf '   - Missing recommended section: %s\n' "${WARNING_MISSING[@]}"
    fi
    if [[ ${#VALIDATION_WARNINGS[@]} -gt 0 ]]; then
        printf '   - %s\n' "${VALIDATION_WARNINGS[@]}"
    fi
    echo ""
fi

# Final verdict
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $MISSING_COUNT -gt 0 || $ERROR_COUNT -gt 0 ]]; then
    echo "❌ VALIDATION FAILED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Report is incomplete. Please address the errors above before closing the phase."
    echo ""
    exit 1
elif [[ $WARNING_COUNT -gt 0 ]]; then
    echo "⚠️  VALIDATION PASSED WITH WARNINGS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Report is complete but has some recommended improvements."
    echo "Consider addressing warnings for best quality."
    echo ""
    exit 0
else
    echo "✅ VALIDATION PASSED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Report is complete and ready for phase closure."
    echo ""
    echo "Next step: Extract lessons learned to central knowledge base:"
    echo "  → .specify/scripts/bash/extract-lessons-learned.sh"
    echo ""
    exit 0
fi
