#!/usr/bin/env bash
# =============================================================================
# ingest.sh — Source material import helper
# Usage:   bash scripts/ingest.sh <file-path | URL>
# Purpose: Normalise and copy a new source into raw/sources/, then print the
#          LLM Agent prompt to trigger the INGEST workflow.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
RAW_SOURCES="$ROOT/raw/sources"
INPUT="${1:-}"

if [[ -z "$INPUT" ]]; then
  echo "Usage: bash scripts/ingest.sh <file-path | URL>"
  echo ""
  echo "Examples:"
  echo "  bash scripts/ingest.sh ~/Downloads/paper.pdf"
  echo "  bash scripts/ingest.sh https://example.com/article"
  echo "  bash scripts/ingest.sh ~/notes/meeting-2026-04-28.md"
  exit 1
fi

TODAY=$(date +%Y-%m-%d)

# ── URL handling ──────────────────────────────────────────────────────────────
if [[ "$INPUT" =~ ^https?:// ]]; then
  echo "Detected URL, attempting download..."

  if ! command -v curl &>/dev/null; then
    echo "Error: curl is required. Download the file manually and re-run."
    exit 1
  fi

  SLUG=$(echo "$INPUT" | sed 's|https\?://||' | sed 's|[/?.=&]|-|g' | cut -c1-60)
  OUTFILE="$RAW_SOURCES/${TODAY}-${SLUG}.md"

  echo "Downloading to: $OUTFILE"

  if command -v pandoc &>/dev/null; then
    curl -s "$INPUT" | pandoc -f html -t markdown -o "$OUTFILE" 2>/dev/null || \
      { echo "  Warning: pandoc conversion failed, saving raw HTML"; curl -s "$INPUT" > "$OUTFILE"; }
  else
    curl -s "$INPUT" > "$OUTFILE"
    echo "  Tip: install pandoc for better HTML-to-Markdown conversion"
  fi

# ── Local file handling ───────────────────────────────────────────────────────
else
  if [[ ! -f "$INPUT" ]]; then
    echo "Error: file not found: $INPUT"
    exit 1
  fi

  FILENAME=$(basename "$INPUT")
  EXT="${FILENAME##*.}"
  BASENAME="${FILENAME%.*}"

  # Normalise filename: lowercase, spaces to hyphens, remove non-alphanumeric
  NORMALIZED=$(echo "$BASENAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | sed 's/[^a-z0-9-]//g')

  case "$EXT" in
    md|txt)
      OUTFILE="$RAW_SOURCES/${TODAY}-${NORMALIZED}.md"
      cp "$INPUT" "$OUTFILE"
      ;;
    pdf)
      OUTFILE="$RAW_SOURCES/${TODAY}-${NORMALIZED}.pdf"
      cp "$INPUT" "$OUTFILE"
      echo "  PDF copied. Tell the LLM Agent to read this PDF file."
      ;;
    *)
      OUTFILE="$RAW_SOURCES/${TODAY}-${NORMALIZED}.${EXT}"
      cp "$INPUT" "$OUTFILE"
      ;;
  esac

  echo "Copied to: $OUTFILE"
fi

REL_PATH="${OUTFILE#$ROOT/}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Copy the following prompt to your LLM Agent:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please process new source material: \`$REL_PATH\`"
echo ""
echo "Follow the INGEST workflow defined in LLM.md:"
echo "1. Read and understand the content"
echo "2. Report 3-5 key findings"
echo "3. Create a source summary page and related entity/concept pages"
echo "4. Update index.md and log.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
