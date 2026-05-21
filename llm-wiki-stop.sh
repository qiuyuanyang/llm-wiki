#!/usr/bin/env bash
# =============================================================================
# LLM Wiki 停止脚本
# =============================================================================
# 停止 wiki_watcher 和 web_ui
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 LLM Wiki 停止"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 停止 wiki_watcher
if [[ -f "$SCRIPT_DIR/.wiki_watcher.pid" ]]; then
    pid=$(cat "$SCRIPT_DIR/.wiki_watcher.pid")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null && echo "✅ wiki_watcher 已停止 (PID: $pid)"
    else
        echo "⚠  残留 PID 文件，已清理"
    fi
    rm -f "$SCRIPT_DIR/.wiki_watcher.pid"
else
    # 有时 PID 文件可能丢失，尝试查找
    if pgrep -f "wiki_watcher.py" >/dev/null 2>&1; then
        echo "✅ wiki_watcher 已停止（旧 PID 文件不存在）"
    fi
fi

# 停止 web_ui
if [[ -f "$SCRIPT_DIR/.web_ui.pid" ]]; then
    pid=$(cat "$SCRIPT_DIR/.web_ui.pid")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null && echo "✅ Web UI 已停止 (PID: $pid)"
    else
        echo "⚠  残留 PID 文件，已清理"
    fi
    rm -f "$SCRIPT_DIR/.web_ui.pid"
else
    # 有时 PID 文件可能丢失，尝试查找
    if pgrep -f "web_ui.py" >/dev/null 2>&1; then
        echo "✅ Web UI 已停止（旧 PID 文件不存在）"
    fi
fi

echo ""
echo "✅ 所有服务已停止"
