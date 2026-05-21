#!/usr/bin/env bash
# =============================================================================
# stats.sh — Wiki 统计报告和健康检查
# Usage:   bash scripts/stats.sh [--lint]
# Purpose: 快速查看 wiki 状态; 为 LLM 生成健康检查报告
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

echo "Wiki 统计报告"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "生成时间: $(date '+%Y-%m-%d %H:%M')"
echo ""

# ── 基本统计 ──────────────────────────────────────────────────────────────
count_files() { find "$1" -name "*.md" 2>/dev/null | wc -l | tr -d ' '; }

TOTAL_WIKI=$(count_files "$WIKI")
ENTITIES=$(count_files "$WIKI/entities")
CONCEPTS=$(count_files "$WIKI/concepts")
SOURCES_WIKI=$(count_files "$WIKI/sources")
QUERIES=$(count_files "$WIKI/queries" 2>/dev/null || echo 0)
RAW_COUNT=$(find "$RAW" -type f 2>/dev/null | wc -l | tr -d ' ')

echo "内容统计"
echo "  原始源文件:    $RAW_COUNT"
echo "  Wiki 总页面:   $TOTAL_WIKI"
echo "  ├─ 实体:       $ENTITIES"
echo "  ├─ 概念:       $CONCEPTS"
echo "  ├─ 源摘要:     $SOURCES_WIKI"
echo "  └─ 查询归档:   $QUERIES"
echo ""

# ── 最近操作日志 ────────────────────────────────────────────────────────
if [[ -f "$WIKI/log.md" ]]; then
  echo "最近操作 (log.md)"
  grep "^## \[" "$WIKI/log.md" 2>/dev/null | tail -5 | sed 's/^/  /' || echo "  (无记录)"
  echo ""
fi

# ── 健康检查 ──────────────────────────────────────────────────────────────
if $LINT_MODE; then
  echo "健康检查"
  echo "──────────────────────────────────────"

  echo ""
  echo "[警告] 可能的孤立页面（没有出站 [[链接]]）:"
  find "$WIKI/entities" "$WIKI/concepts" -name "*.md" 2>/dev/null | while read -r f; do
    if ! grep -q '\[\[' "$f" 2>/dev/null; then
      echo "  - ${f#$ROOT/}"
    fi
  done || echo "  OK: 没有孤立页面"

  echo ""
  echo "[错误] 缺少前置元数据的页面:"
  find "$WIKI" -name "*.md" -not -name "index.md" -not -name "log.md" 2>/dev/null | while read -r f; do
    if ! head -1 "$f" | grep -q "^---"; then
      echo "  - ${f#$ROOT/}"
    fi
  done || echo "  OK: 所有页面都有前置元数据"

  echo ""
  echo "[警告] 可能尚未导入的原始源文件:"
  find "$RAW" -type f 2>/dev/null | while read -r raw_file; do
    basename_noext=$(basename "$raw_file" | sed 's/\.[^.]*$//')
    if ! find "$WIKI/sources" -name "${basename_noext}*" 2>/dev/null | grep -q .; then
      echo "  - ${raw_file#$ROOT/}"
    fi
  done || echo "  OK: 所有原始源文件都已导入"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "将以下提示词复制给你的 LLM Agent 进行深度检查:"
  echo ""
  echo "请对这个 wiki 运行 LINT 健康检查。"
  echo "重点关注: 矛盾内容、过时信息、缺失的关键概念页面、损坏的链接。"
  echo "输出格式: 问题列表，每项包含严重级别（error/warn/ok）和修复建议。"
fi

echo ""
echo "提示: 运行 \`bash scripts/stats.sh --lint\` 获取完整健康检查报告"
