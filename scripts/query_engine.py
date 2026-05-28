#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
query_engine.py — Intelligent Q&A engine combining vector search + LLM synthesis.

Usage:
    python3 scripts/query_engine.py "What is the IP of web-server-01?"
    python3 scripts/query_engine.py --wiki-only "How to configure MySQL replication?"
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import WikiConfig
from vector_store import VectorStore
from embedding_client import EmbeddingClient


class QueryEngine:
    """Vector search + LLM synthesis for intelligent Q&A."""

    def __init__(self, config: Optional[WikiConfig] = None):
        self.config = config or WikiConfig()
        self.store = VectorStore(self.config)
        self.embedding_client = EmbeddingClient(self.config)
        self.router = None  # Lazy-loaded from wiki_watcher

    def _get_router(self):
        """Lazy-load ModelRouter from wiki_watcher module."""
        if self.router is None:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
            from wiki_watcher import ModelRouter
            self.router = ModelRouter(self.config.wiki_root)
        return self.router

    def _read_page_content(self, page_path: str) -> str:
        """Read a wiki page's content."""
        full_path = self.config.wiki_root / page_path
        if not full_path.exists():
            return f"[Page not found: {page_path}]"

        content = full_path.read_text(encoding="utf-8")
        # Strip frontmatter for context
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        return content.strip()

    def query(self, question: str, top_k: int = 8,
              wiki_only: bool = False) -> dict:
        """
        Execute a query: vector search → LLM synthesis.

        Returns:
            {
                "question": "...",
                "answer": "...",
                "sources": [{"path": "...", "title": "...", "score": 0.xx}],
                "raw_results": [...]
            }
        """
        # Step 1: Generate embedding for the question
        query_vector = self.embedding_client.embed_single(question)

        # Step 2: Vector search to find relevant pages
        results = self.store.search(query_vector, top_k=top_k)

        if not results:
            return {
                "question": question,
                "answer": "在知识库中未找到相关内容。请先导入源材料。",
                "sources": [],
            }

        # Step 3: Read relevant page contents
        context_parts = []
        sources = []
        for result in results:
            content = self._read_page_content(result["page_path"])
            if content and not content.startswith("[Page not found"):
                context_parts.append(
                    f"=== {result['title']} ({result['page_path']}, score: {result['score']:.3f}) ===\n"
                    f"{content}"
                )
                sources.append({
                    "path": result["page_path"],
                    "title": result["title"],
                    "score": round(result["score"], 4),
                })

        if not context_parts:
            return {
                "question": question,
                "answer": "找到相关页面但无法读取内容。",
                "sources": [],
            }

        context = "\n\n".join(context_parts)

        # Step 4: LLM synthesis
        router = self._get_router()

        system_prompt = f"""你是一个基础设施和IT运维知识库的智能问答助手。

请根据提供的 wiki 页面内容回答用户的问题。回答要准确、简洁，并标注信息来源。

规则：
1. 仅使用提供的 wiki 内容回答问题，不要编造信息。
2. 用以下格式标注来源：[来源: page_path]
3. 如果 wiki 中没有足够信息，请明确说明。
4. 基础设施相关问题请包含具体细节（IP地址、配置信息、依赖关系等）。
5. 如果多个来源存在冲突，请指出冲突并分别标注来源。
6. 用清晰的 Markdown 格式组织回答。
7. 所有描述性语言（标题、解释、总结等）必须使用中文回答，但源数据内容（代码、配置、命令等）保持原文不变。

Mermaid 图表规则（如果用户要求画图）：
- 使用 ```mermaid 代码块包裹
- 只使用 mermaid v10 兼容语法，禁止使用以下 v11+ 特性：
  - 禁止在 subgraph 内使用 direction 语句
  - 禁止使用 classDef + class 语句（改用 style 语句）
  - 禁止在节点标签中使用 ~ 符号
- 使用以下基本语法：
  - 节点: NodeID[显示文本] 或 NodeID((显示文本))
  - 连接: A --> B 或 A -.-> B（虚线）
  - 子图: subgraph 名称  ... end
  - 样式: style NodeID fill:#颜色,stroke:#颜色,stroke-width:2px
- 确保所有括号 [] () \"\" 配对闭合
- graph 代码块结束后再写说明文字，不要混在一起"""

        user_message = f"""问题: {question}

---
相关 wiki 页面:
{context[:12000]}"""

        try:
            answer = router.call(system_prompt, user_message, max_tokens=4000)
            # Strip thinking blocks
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        except Exception as e:
            answer = f"生成回答时出错: {e}\n\n以下是相关页面:\n" + "\n".join(
                f"- [{s['title']}]({s['path']}) (相关度: {s['score']})" for s in sources
            )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    def search_only(self, query: str, top_k: int = 10) -> list:
        """Vector search only, without LLM synthesis."""
        query_vector = self.embedding_client.embed_single(query)
        return self.store.search(query_vector, top_k=top_k)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wiki 智能问答引擎")
    parser.add_argument("question", help="要问的问题")
    parser.add_argument("--top-k", type=int, default=8, help="检索结果数量")
    parser.add_argument("--wiki-only", action="store_true", help="仅搜索 wiki 页面")
    parser.add_argument("--search-only", action="store_true", help="仅向量搜索，不调用 LLM")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    engine = QueryEngine()

    if args.search_only:
        results = engine.search_only(args.question, top_k=args.top_k)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"🔍 搜索: {args.question}")
            print("━" * 50)
            if not results:
                print("  未找到相关结果")
            else:
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r['title']} ({r['page_path']}) — 相关度: {r['score']:.4f}")
    else:
        result = engine.query(args.question, top_k=args.top_k, wiki_only=args.wiki_only)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❓ 问题: {result['question']}")
            print("\n📝 回答:\n")
            print(result["answer"])
            print("\n📚 参考来源:")
            for s in result.get("sources", []):
                print(f"  • {s['title']} ({s['path']}) — 相关度: {s['score']}")


if __name__ == "__main__":
    main()
