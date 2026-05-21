#!/usr/bin/env bash
# =============================================================================
# start.sh — LLM Wiki 一键启动脚本
# =============================================================================
# 启动以下三个服务：
#   1. wiki_watcher → 自动监控 raw/ 目录，新文件自动处理
#   2. web_ui       → Web 界面 (http://localhost:5000)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PIDFILE_WATCHER="$SCRIPT_DIR/.wiki_watcher.pid"
PIDFILE_WEB="$SCRIPT_DIR/.web_ui.pid"
LOG_W="$SCRIPT_DIR/wiki_watcher.log"
LOG_WEB="$SCRIPT_DIR/web_ui.log"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 LLM Wiki 启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 启动 wiki_watcher 守护进程
if [[ -f "$PIDFILE_WATCHER" ]]; then
    OLD_PID=$(cat "$PIDFILE_WATCHER")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "✅ wiki_watcher 已在运行 (PID: $OLD_PID)"
    else
        echo "⚠  残留 PID 文件，清理重新..."
        rm -f "$PIDFILE_WATCHER"
        python3 scripts/wiki_watcher.py --daemon
        sleep 1
        NEW_PID=$(cat "$PIDFILE_WATCHER" 2>/dev/null)
        echo "✅ wiki_watcher 已启动 (PID: $NEW_PID)"
    fi
else
    python3 scripts/wiki_watcher.py --daemon
    sleep 1
    PID=$(cat "$PIDFILE_WATCHER" 2>/dev/null)
    echo "✅ wiki_watcher 已启动 (PID: $PID)"
fi

# 2. 启动 web_ui
if [[ -f "$PIDFILE_WEB" ]]; then
    OLD_PID=$(cat "$PIDFILE_WEB")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "✅ Web UI 已在运行 (PID: $OLD_PID, 端口 5000)"
    else
        echo "⚠  残留 PID 文件，清理重新..."
        rm -f "$PIDFILE_WEB"
        nohup python3 scripts/web_ui.py --port 5000 > web_ui.log 2>&1 & echo $! > .web_ui.pid
        sleep 2
        NEW_PID=$(cat .web_ui.pid 2>/dev/null)
        echo "✅ Web UI 已启动 (PID: $NEW_PID, 端口 5000)"
    fi
else
    nohup python3 scripts/web_ui.py --port 5000 > web_ui.log 2>&1 & echo $! > .web_ui.pid
    sleep 2
    PID=$(cat .web_ui.pid 2>/dev/null)
    echo "✅ Web UI 已启动 (PID: $PID, 端口 5000)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "服务概览"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔍 wiki_watcher  → raw/ 实时监控 (on-the-fly)"
echo "  🌐 Web UI           → http://localhost:5000"
echo ""
echo "日志查看:"
echo "  tail -f wiki_watcher.log   # wiki_watcher 日志"
echo "  tail -f web_ui.log         # Web UI 日志"
echo ""
echo "管理命令:"
echo "  ./stop.sh          # 停止所有服务"
echo "  ./status.sh        # 查看运行状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
