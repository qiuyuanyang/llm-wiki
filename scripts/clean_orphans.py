#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
clean_orphans.py — 异步清理向量库中的孤儿条目

用法:
    python3 scripts/clean_orphans.py          # 立即执行
    python3 scripts/clean_orphans.py --cron   # cron 模式（安静输出）

此脚本可加入 crontab 每天凌晨自动运行:
    0 3 * * * cd /home/gpt/llm-wiki && python3 scripts/clean_orphans.py --cron >> web_ui.log 2>&1
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import WikiConfig
from vector_store import VectorStore
from scripts.vector_ingest import _clean_orphan_vectors


def main():
    parser = argparse.ArgumentParser(description="Clean orphan vector entries")
    parser.add_argument("--cron", action="store_true", help="Quiet mode for cron")
    args = parser.parse_args()

    config = WikiConfig()
    show = not args.cron

    if show:
        print("🔍 开始扫描孤儿向量条目...")

    orphaned = _clean_orphan_vectors(config, show_progress=show)

    if show:
        if orphaned:
            print(f"✅ 清理完成，共删除 {len(orphaned)} 个孤儿条目")
        else:
            print("✅ 向量库干净，无需清理")
    else:
        # --cron 模式：只在有清理动作时输出，避免日志噪音
        if orphaned:
            print(f"[clean_orphans] cleaned {len(orphaned)} orphans: {', '.join(orphaned)}")


if __name__ == "__main__":
    main()
