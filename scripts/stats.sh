#!/usr/bin/env bash
# =============================================================================
# stats.sh — Wiki statistics and health check
# Usage:   bash scripts/stats.sh [--lint]
# Purpose: Quick overview of wiki state; generates a lint report for the LLM.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
WIKI="$ROOT/wiki"
RAW="$ROOT/raw/sources"
LINT_MODE=false

for arg in "$@"; do
  [[ "$arg" == "--lint" ]] && LINT_MODE=true
done

echo "Wiki Statistics Report"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Generated: $(date '+%Y-%m-%d %H:%M')"
echo ""

# ── Basic counts ──────────────────────────────────────────────────────────────
count_files() { find "$1" -name "*.md" 2>/dev/null | wc -l | tr -d ' '; }

TOTAL_WIKI=$(count_files "$WIKI")
ENTITIES=$(count_files "$WIKI/entities")
CONCEPTS=$(count_files "$WIKI/concepts")
SOURCES_WIKI=$(count_files "$WIKI/sources")
QUERIES=$(count_files "$WIKI/queries" 2>/dev/null || echo 0)
RAW_COUNT=$(find "$RAW" -type f 2>/dev/null | wc -l | tr -d ' ')

echo "Content counts"
echo "  Raw source files:  $RAW_COUNT"
echo "  Wiki total pages:  $TOTAL_WIKI"
echo "  ├─ Entities:       $ENTITIES"
echo "  ├─ Concepts:       $CONCEPTS"
echo "  ├─ Sources:        $SOURCES_WIKI"
echo "  └─ Queries:        $QUERIES"
echo ""

# ── Recent log entries ────────────────────────────────────────────────────────
if [[ -f "$WIKI/log.md" ]]; then
  echo "Recent operations (log.md)"
  grep "^## \[" "$WIKI/log.md" 2>/dev/null | tail -5 | sed 's/^/  /' || echo "  (no entries)"
  echo ""
fi

# ── Lint checks ───────────────────────────────────────────────────────────────
if $LINT_MODE; then
  echo "Lint checks"
  echo "──────────────────────────────────────"

  echo ""
  echo "[warn] Possible orphaned pages (no outbound [[links]]):"
  find "$WIKI/entities" "$WIKI/concepts" -name "*.md" 2>/dev/null | while read -r f; do
    if ! grep -q '\[\[' "$f" 2>/dev/null; then
      echo "  - ${f#$ROOT/}"
    fi
  done || echo "  OK: no orphaned pages"

  echo ""
  echo "[error] Pages missing frontmatter:"
  find "$WIKI" -name "*.md" -not -name "index.md" -not -name "log.md" 2>/dev/null | while read -r f; do
    if ! head -1 "$f" | grep -q "^---"; then
      echo "  - ${f#$ROOT/}"
    fi
  done || echo "  OK: all pages have frontmatter"

  echo ""
  echo "[warn] Raw source files possibly not yet ingested:"
  find "$RAW" -type f 2>/dev/null | while read -r raw_file; do
    basename_noext=$(basename "$raw_file" | sed 's/\.[^.]*$//')
    if ! find "$WIKI/sources" -name "${basename_noext}*" 2>/dev/null | grep -q .; then
      echo "  - ${raw_file#$ROOT/}"
    fi
  done || echo "  OK: all raw sources have been ingested"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Copy the following prompt to your LLM Agent for a deep lint:"
  echo ""
  echo "Please run a LINT health check on this wiki."
  echo "Focus on: contradictory content, stale information, missing key concept pages, broken links."
  echo "Output format: a list of issues, each with severity (error/warn/ok) and a fix suggestion."
fi

echo ""
echo "Tip: run \`bash scripts/stats.sh --lint\` for the full health check report"
