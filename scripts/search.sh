#!/usr/bin/env bash
# =============================================================================
# search.sh — Wiki 语义搜索（带 Markdown 渲染）
# Usage:   bash scripts/search.sh "关键词" [--wiki-only] [--raw-only]
# Purpose: 在 wiki 中搜索相关内容，以结构化格式展示结果
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
  echo "用法: bash scripts/search.sh \"关键词\" [--wiki-only] [--raw-only]"
  exit 1
fi

echo ""
echo "🔍 搜索: \"$QUERY\""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 搜索单个目录
search_dir() {
  local dir="$1"
  local label="$2"
  local count=0

  echo ""
  echo "━━━ $label ━━━"

  # 获取匹配文件
  local files=()
  while IFS= read -r file; do
    files+=("$file")
  done < <(grep -ril "$QUERY" "$dir" --include="*.md" 2>/dev/null | head -20)

  if [[ ${#files[@]} -eq 0 ]]; then
    echo "  未找到相关结果"
    return
  fi

  for file in "${files[@]}"; do
    local rel_path="${file#$ROOT/}"
    local name=$(basename "$file" .md | tr '-' ' ' | tr '_' ' ')
    # 提取标题行
    local title=$(grep -m1 '^# ' "$file" 2>/dev/null | sed 's/^# //' || echo "$name")
    # 提取匹配行（最多3行，带上下文）
    local matches=$(grep -in -A1 -B0 "$QUERY" "$file" 2>/dev/null | head -6)

    echo ""
    echo "  📄 [$name] $rel_path"
    if [[ -n "$title" && "$title" != "$name" ]]; then
      echo "     标题: $title"
    fi
    if [[ -n "$matches" ]]; then
      echo "     匹配内容:"
      while IFS= read -r line; do
        echo "       $line"
      done <<< "$matches"
    fi
    count=$((count + 1))
  done

  echo ""
  echo "  共找到 $count 个匹配文件"
}

case $MODE in
  wiki) search_dir "$WIKI" "Wiki 页面" ;;
  raw)  search_dir "$RAW"  "原始源文件" ;;
  all)
    search_dir "$WIKI" "Wiki 页面"
    search_dir "$RAW"  "原始源文件"
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=$(grep -ril "$QUERY" "$ROOT" --include="*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "✅ 共找到 $TOTAL 个匹配文件"
echo ""
echo "💡 提示: 将文件路径分享给 LLM Agent 可获取综合分析回答"
echo ""
