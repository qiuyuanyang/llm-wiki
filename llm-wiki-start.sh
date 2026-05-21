#!/usr/bin/env bash
# =============================================================================
# LLM Wiki 一键启动脚本
# =============================================================================
# 启动以下两个服务：
#   1. wiki_watcher  → 后台守护进程，自动监控 raw/sources/ 新文件并 LLM 处理
#   2. web_ui        → Web 界面 (端口 5000)
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---- Helper functions ----

is_running() {
    local pidfile="$1"
    if [[ -f "$pidfile" ]]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        # Dead PID file
        rm -f "$pidfile"
    fi
    return 1
}

# ---- Start wiki_watcher ----

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 LLM Wiki 启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Wiki Watcher 守护进程
echo "→ 启动 wiki_watcher..."
if is_running "$SCRIPT_DIR/.wiki_watcher.pid"; then
    pid=$(cat "$SCRIPT_DIR/.wiki_watcher.pid")
    echo "  ⚠  已在运行 (PID: $pid)"
else
    nohup python3 scripts/wiki_watcher.py --daemon > /dev/null 2>&1 &
    sleep 2
    if is_running "$SCRIPT_DIR/.wiki_watcher.pid"; then
        pid=$(cat "$SCRIPT_DIR/.wiki_watcher.pid")
        echo "  ✅ wiki_watcher 已启动 (PID: $pid)"
    else
        echo "  ❌ wiki_watcher 启动失败，查看日志："
        echo "     cat $SCRIPT_DIR/wiki_watcher.log"
        exit 1
    fi
fi

echo ""

# 2. Web UI
echo "→ 启动 Web UI (端口 5000)..."
if is_running "$SCRIPT_DIR/.web_ui.pid"; then
    pid=$(cat "$SCRIPT_DIR/.web_ui.pid")
    echo "  ⚠  已在运行 (PID: $pid)"
else
    nohup python3 scripts/web_ui.py --port 5000 >> web_ui.log 2>&1 &
    echo $! > "$SCRIPT_DIR/.web_ui.pid"
    sleep 2
    if is_running "$SCRIPT_DIR/.web_ui.pid"; then
        pid=$(cat "$SCRIPT_DIR/.web_ui.pid")
        echo "  ✅ Web UI 已启动 (PID: $pid)"
    else
        echo "  ❌ Web UI 启动失败，查看日志："
        echo "     cat $SCRIPT_DIR/web_ui.log"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 所有服务已启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🔍 wiki_watcher     → 自动监控 raw/ 目录"
echo "  🌐 Web UI           → http://localhost:5000"
echo ""
echo "其他操作:"
echo "  ./stop.sh          → 停止所有服务"
echo "  ./wiki.sh status   → 查看运行状态和模型"
echo "  tail -f wiki_watcher.log  → 查看 watcher 日志"
echo "  tail -f web_ui.log        → 查看 Web UI 日志"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
