#!/usr/bin/env bash
# =============================================================================
# wiki.sh — LLM Wiki 统一 CLI
# Usage: ./wiki.sh <command> [args]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "${1:-help}" in
  daemon|start-bg)
    python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --daemon
    ;;
  start)
    python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR"
    ;;
  stop)
    python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --stop
    ;;
  status)
    python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --status
    ;;
  hotspot)
    python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --hotspot
    ;;
  ingest)
    bash "$SCRIPT_DIR/scripts/ingest.sh" "${2:-}"
    ;;
  stats)
    bash "$SCRIPT_DIR/scripts/stats.sh"
    ;;
  lint)
    bash "$SCRIPT_DIR/scripts/stats.sh" --lint
    ;;
  search)
    bash "$SCRIPT_DIR/scripts/search.sh" "${2:-}" --wiki-only
    ;;
  model)
    # 切换模型: ./wiki.sh model local,Qwen3.6-35B-A3B-FP8
    #           ./wiki.sh model dashscope,qwen-max
    #           ./wiki.sh model anthropic,claude-sonnet-4-6
    #           ./wiki.sh model          (无参数 → 显示当前模型)
    if [[ -z "${2:-}" ]]; then
      python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --status
    else
      python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --model "${2}"
    fi
    ;;
  embed)
    # 为所有 wiki 页面生成向量嵌入
    python3 "$SCRIPT_DIR/scripts/vector_ingest.py"
    ;;
  reindex)
    # 完全重建索引: 清除向量并重新生成
    python3 "$SCRIPT_DIR/scripts/vector_ingest.py" --reindex
    ;;
  query)
    # 智能问答: ./wiki.sh query "MySQL 主从复制如何配置？"
    python3 "$SCRIPT_DIR/scripts/query_engine.py" "${2:-}"
    ;;
  search-v)
    # 仅向量搜索: ./wiki.sh search-v "MySQL 主从复制"
    python3 "$SCRIPT_DIR/scripts/query_engine.py" "${2:-}" --search-only
    ;;
  graph)
    # 生成拓扑图
    python3 "$SCRIPT_DIR/scripts/graph_viz.py" --output "$SCRIPT_DIR/wiki/topology.html"
    ;;
  diagnose)
    # 诊断引擎: scan/search/list/stats
    python3 "$SCRIPT_DIR/scripts/diagnosis_engine.py" "${2:-scan}" "${3:-}"
    ;;
  web)
    # 启动 Web UI: ./wiki.sh web [--port 5000]
    python3 "$SCRIPT_DIR/scripts/web_ui.py" "${@:2}"
    ;;
  help|*)
    echo "用法: ./wiki.sh <command>"
    echo ""
    echo "命令:"
    echo "  daemon             启动后台守护进程（全自动模式）"
    echo "  start              启动前台监视器（实时日志可见）"
    echo "  stop               停止后台守护进程"
    echo "  status             显示运行状态和当前模型"
    echo "  hotspot            立即生成热点分析"
    echo "  ingest <file|URL>  手动导入源材料到 raw/sources/"
    echo "  stats              显示 wiki 统计信息"
    echo "  lint               运行健康检查"
    echo "  search <关键词>     搜索 wiki 内容"
    echo ""
    echo "  model [SPEC]       查看或切换当前模型"
    echo "    格式: provider,model_name"
    echo "    示例:"
    echo "      ./wiki.sh model local,Qwen3.6-35B-A3B-FP8"
    echo "      ./wiki.sh model dashscope,qwen-max"
    echo "      ./wiki.sh model anthropic,claude-opus-4-6"
    echo "      ./wiki.sh model anthropic,claude-sonnet-4-6"
    echo ""
    echo "  embed              为所有 wiki 页面生成向量嵌入"
    echo "  reindex            完全重建索引: 清除向量并重新生成"
    echo "  query <问题>       智能问答（向量搜索 + LLM）"
    echo "  search-v <关键词>   仅向量搜索（不调用 LLM）"
    echo "  graph              生成拓扑图（HTML）"
    echo "  diagnose <cmd>     诊断引擎（scan/search/list/stats）"
    echo "  web [--port PORT]  启动 Web UI（默认端口 5000）"
    echo ""
    echo "  内置提供商:"
    echo "    anthropic  → ANTHROPIC_API_KEY"
    echo "    local      → http://localhost:11434/v1 (Ollama / vLLM)"
    echo "    dashscope  → DASHSCOPE_API_KEY"
    echo "    openai     → OPENAI_API_KEY"
    echo "    自定义: 在 wiki_config.json 的 'providers' 下添加新提供商"
    ;;
esac
