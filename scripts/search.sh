#!/usr/bin/env bash
# =============================================================================
# search.sh — Local wiki full-text search
# Usage:   bash scripts/search.sh "keyword" [--wiki-only] [--raw-only]
# Purpose: Quickly locate relevant pages to help the LLM navigate a large wiki.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
WIKI="$ROOT/wiki"
RAW="$ROOT/raw"

QUERY="${1:-}"
MODE="all"  # all | wiki | raw

for arg in "$@"; do
  case $arg in
    --wiki-only) MODE="wiki" ;;
    --raw-only)  MODE="raw"  ;;
  esac
done

if [[ -z "$QUERY" ]]; then
  echo "Usage: bash scripts/search.sh \"keyword\" [--wiki-only] [--raw-only]"
  exit 1
fi

echo "Searching: \"$QUERY\""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

search_dir() {
  local dir="$1"
  local label="$2"
  echo ""
  echo "$label"
  echo "──────────────────────────────────────"

  if grep -ril "$QUERY" "$dir" --include="*.md" 2>/dev/null | head -20 | while read -r file; do
    echo ""
    echo "  ${file#$ROOT/}"
    grep -in "$QUERY" "$file" | head -3 | while read -r line; do
      echo "     $line"
    done
  done; then
    :
  else
    echo "  (no results)"
  fi
}

case $MODE in
  wiki) search_dir "$WIKI" "Wiki pages" ;;
  raw)  search_dir "$RAW"  "Raw sources" ;;
  all)
    search_dir "$WIKI" "Wiki pages"
    search_dir "$RAW"  "Raw sources"
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=$(grep -ril "$QUERY" "$ROOT" --include="*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "Found $TOTAL matching files"
echo ""
echo "Tip: share the file paths above with your LLM Agent to get a synthesised answer"
