#!/usr/bin/env bash
# =============================================================================
# wiki.sh — LLM Wiki unified CLI
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
    # Switch model: ./wiki.sh model local,Qwen3.6-35B-A3B-FP8
    #               ./wiki.sh model dashscope,qwen-max
    #               ./wiki.sh model anthropic,claude-sonnet-4-6
    #               ./wiki.sh model          (no argument → show current model)
    if [[ -z "${2:-}" ]]; then
      python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --status
    else
      python3 "$SCRIPT_DIR/scripts/wiki_watcher.py" --root "$SCRIPT_DIR" --model "${2}"
    fi
    ;;
  help|*)
    echo "Usage: ./wiki.sh <command>"
    echo ""
    echo "Commands:"
    echo "  daemon             Start background daemon (fully automatic mode)"
    echo "  start              Start foreground watcher (real-time logs visible)"
    echo "  stop               Stop background daemon"
    echo "  status             Show running status and active model"
    echo "  hotspot            Generate hotspot analysis immediately"
    echo "  ingest <file|URL>  Manually import source material into raw/sources/"
    echo "  stats              Show wiki statistics"
    echo "  lint               Run health check"
    echo "  search <keyword>   Search wiki content"
    echo ""
    echo "  model [SPEC]       View or switch the active model"
    echo "    Format: provider,model_name"
    echo "    Examples:"
    echo "      ./wiki.sh model local,Qwen3.6-35B-A3B-FP8"
    echo "      ./wiki.sh model dashscope,qwen-max"
    echo "      ./wiki.sh model anthropic,claude-opus-4-6"
    echo "      ./wiki.sh model anthropic,claude-sonnet-4-6"
    echo ""
    echo "  Built-in providers:"
    echo "    anthropic  → ANTHROPIC_API_KEY"
    echo "    local      → http://localhost:11434/v1 (Ollama / vLLM)"
    echo "    dashscope  → DASHSCOPE_API_KEY"
    echo "    openai     → OPENAI_API_KEY"
    echo "    Custom: add a new provider under 'providers' in wiki_config.json"
    ;;
esac
