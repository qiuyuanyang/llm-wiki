#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
diagnosis_engine.py — Fault diagnosis knowledge base.

Extracts problem → cause → solution triples from wiki sources and provides
diagnostic search.

Usage:
    python3 scripts/diagnosis_engine.py scan     # Scan sources for diagnosis triples
    python3 scripts/diagnosis_engine.py search "MySQL replication lag"
    python3 scripts/diagnosis_engine.py list     # List all diagnoses
"""

import json
import re
import sys
import sqlite3
import math
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import WikiConfig
from embedding_client import EmbeddingClient


class DiagnosisDB:
    """SQLite-backed diagnosis knowledge store."""

    def __init__(self, config: Optional[WikiConfig] = None):
        self.config = config or WikiConfig()
        self.db_path = self.config.wiki_root / ".wiki_diagnoses.db"
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symptom TEXT NOT NULL,
                cause TEXT NOT NULL,
                solution TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'historical',
                source_file TEXT,
                source_page TEXT,
                tags TEXT DEFAULT '[]',
                vector_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_diagnoses_symptom ON diagnoses(symptom)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_diagnoses_severity ON diagnoses(severity)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_diagnoses_status ON diagnoses(status)")
        conn.commit()
        conn.close()

    def upsert(self, symptom: str, cause: str, solution: str,
               severity: str = "medium", status: str = "historical",
               source_file: str = "", source_page: str = "",
               tags: List[str] = None, vector: List[float] = None) -> int:
        conn = self._get_conn()
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        vector_json = json.dumps(vector) if vector else None

        existing = conn.execute(
            "SELECT id FROM diagnoses WHERE symptom = ? AND cause = ?",
            (symptom, cause)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE diagnoses
                SET solution = ?, severity = ?, status = ?, source_file = ?,
                    source_page = ?, tags = ?, vector_json = ?, updated_at = ?
                WHERE id = ?
            """, (solution, severity, status, source_file, source_page, tags_json, vector_json, now, existing["id"]))
            did = existing["id"]
        else:
            conn.execute("""
                INSERT INTO diagnoses (symptom, cause, solution, severity, status,
                                       source_file, source_page, tags, vector_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symptom, cause, solution, severity, status, source_file, source_page,
                  tags_json, vector_json, now, now))
            did = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.commit()
        conn.close()
        return did

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """混合搜索：语义 + 关键词匹配。尽力使用语义，没有向量时回退到关键词。"""
        semantic_results = self.search_semantic(query, limit=limit)
        if semantic_results:
            return semantic_results
        return self._keyword_search(query, limit=limit)

    def search_semantic(self, query: str, limit: int = 20) -> List[Dict]:
        """语义搜索：使用向量嵌入。
        
        返回按语义相关性排序的结果。只返回有向量的诊断记录，
        如果没有向量数据则返回空列表（由 search() 兜底关键词搜索）。
        """
        try:
            embedding_client = EmbeddingClient(WikiConfig())
            query_vector = embedding_client.embed_single(query)
        except Exception:
            return []

        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM diagnoses WHERE vector_json IS NOT NULL"
        ).fetchall()
        conn.close()

        if not rows:
            return []

        scored = []
        for r in rows:
            d = dict(r)
            stored = json.loads(d.get("vector_json") or "[]")
            if not stored:
                continue
            score = self._cosine_similarity(query_vector, stored)
            if score > 0.1:  # 低分忽略，避免噪声
                d["score"] = round(score, 4)
                scored.append(d)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def _keyword_search(self, query: str, limit: int = 20) -> List[Dict]:
        """Fallback keyword search."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM diagnoses
            WHERE symptom LIKE ? OR cause LIKE ? OR solution LIKE ?
            ORDER BY
                CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                updated_at DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def list_all(self, severity: str = None, status: str = None,
                 limit: int = 50) -> List[Dict]:
        conn = self._get_conn()
        where = []
        params = []
        if severity:
            where.append("severity = ?")
            params.append(severity)
        if status:
            where.append("status = ?")
            params.append(status)

        sql = "SELECT * FROM diagnoses"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        conn = self._get_conn()
        stats = {"total": 0, "by_severity": {}, "by_status": {}}

        row = conn.execute("SELECT COUNT(*) as cnt FROM diagnoses").fetchone()
        stats["total"] = row["cnt"]

        for row in conn.execute("SELECT severity, COUNT(*) as cnt FROM diagnoses GROUP BY severity").fetchall():
            stats["by_severity"][row["severity"]] = row["cnt"]

        for row in conn.execute("SELECT status, COUNT(*) as cnt FROM diagnoses GROUP BY status").fetchall():
            stats["by_status"][row["status"]] = row["cnt"]

        conn.close()
        return stats


def extract_from_source(file_path: Path, config: WikiConfig) -> List[Dict]:
    """Extract diagnosis triples from a source file using pattern matching."""
    content = file_path.read_text(encoding="utf-8")

    # Strip frontmatter
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

    triples = []

    # Pattern 1: "问题/故障/现象" + "原因" + "解决方案/处理"
    sections = re.split(r'##\s+', content)
    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue

        heading = lines[0].lower()
        body = '\n'.join(lines[1:])

        # Detect problem sections
        is_problem = any(kw in heading for kw in ['问题', '故障', '现象', 'issue', 'error', 'problem'])
        is_cause = any(kw in heading for kw in ['原因', 'cause', 'root cause'])
        is_solution = any(kw in heading for kw in ['解决', '处理', '修复', 'solution', 'fix', 'resolve'])

        if is_problem:
            triples.append({
                "symptom": lines[0].strip('# '),
                "cause": "",
                "solution": "",
                "source_file": str(file_path.name),
            })
        elif is_cause:
            if triples:
                triples[-1]["cause"] = lines[0].strip('# ')
        elif is_solution:
            if triples:
                triples[-1]["solution"] = body.strip()[:500]

    # Pattern 2: Inline "问题: X, 原因: Y, 解决: Z"
    for m in re.finditer(r'(?:问题|故障)[：:]\s*(.+?)(?:\n|$)', content):
        symptom = m.group(1).strip()
        cause_match = re.search(r'(?:原因|根因)[：:]\s*(.+?)(?:\n|$)', content)
        solution_match = re.search(r'(?:解决|处理|修复)[：:]\s*(.+?)(?:\n|$)', content)

        triples.append({
            "symptom": symptom,
            "cause": cause_match.group(1).strip() if cause_match else "",
            "solution": solution_match.group(1).strip() if solution_match else "",
            "source_file": str(file_path.name),
        })

    # Deduplicate
    seen = set()
    unique = []
    for t in triples:
        key = (t["symptom"], t["cause"])
        if key not in seen and t["symptom"]:
            seen.add(key)
            unique.append(t)

    return unique


def scan_sources(config: WikiConfig, db: DiagnosisDB = None) -> int:
    """扫描所有原始源和 wiki 页面，提取诊断三元组并生成向量。"""
    if db is None:
        db = DiagnosisDB(config)

    count = 0

    # 扫描原始源
    if config.raw_dir.exists():
        for f in config.raw_dir.glob("*.md"):
            triples = extract_from_source(f, config)
            for t in triples:
                db.upsert(
                    symptom=t["symptom"],
                    cause=t.get("cause", ""),
                    solution=t.get("solution", ""),
                    source_file=t["source_file"],
                )
                count += 1

    # 扫描 wiki 源摘要
    sources_dir = config.wiki_dir / "sources"
    if sources_dir.exists():
        for f in sources_dir.glob("*.md"):
            triples = extract_from_source(f, config)
            for t in triples:
                db.upsert(
                    symptom=t["symptom"],
                    cause=t.get("cause", ""),
                    solution=t.get("solution", ""),
                    source_page=str(f.relative_to(config.wiki_root)),
                )
                count += 1

    # 生成向量嵌入
    generate_vectors(config, db)

    return count


def generate_vectors(config: WikiConfig, db: DiagnosisDB = None) -> int:
    """为诊断记录生成向量嵌入。"""
    if db is None:
        db = DiagnosisDB(config)

    try:
        embedding_client = EmbeddingClient(config)
    except Exception as e:
        print(f"⚠ 无法初始化嵌入客户端: {e}")
        return 0

    conn = db._get_conn()
    rows = conn.execute(
        "SELECT id, symptom, cause, solution, vector_json FROM diagnoses"
    ).fetchall()
    conn.close()

    updated = 0
    for r in rows:
        d = dict(r)
        # 跳过已有向量的记录
        if d.get("vector_json"):
            continue

        # 组合文本生成嵌入
        text = f"{d['symptom']} {d['cause']} {d['solution']}"
        if not text.strip():
            continue

        try:
            vector = embedding_client.embed_single(text)
            vector_json = json.dumps(vector)
            conn = db._get_conn()
            conn.execute(
                "UPDATE diagnoses SET vector_json = ? WHERE id = ?",
                (vector_json, d["id"])
            )
            conn.commit()
            conn.close()
            updated += 1
        except Exception as e:
            print(f"⚠ 诊断 {d['id']} 向量生成失败: {e}")

    return updated


def main():
    import argparse
    parser = argparse.ArgumentParser(description="诊断知识引擎")
    parser.add_argument("command", choices=["scan", "search", "list", "stats", "embed"],
                        help="要运行的命令")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词")
    parser.add_argument("--severity", choices=["critical", "high", "medium", "low"],
                        help="按严重级别筛选")
    parser.add_argument("--status", choices=["resolved", "ongoing", "historical"],
                        help="按状态筛选")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    config = WikiConfig()
    db = DiagnosisDB(config)

    if args.command == "scan":
        count = scan_sources(config, db)
        stats = db.get_stats()
        print(f"✅ 扫描完成: 提取了 {count} 条新三元组")
        print(f"   数据库中共: {stats['total']}")
        for sev, cnt in stats.get("by_severity", {}).items():
            print(f"   {sev}: {cnt}")

    elif args.command == "search":
        results = db.search(args.query)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            if not results:
                print("未找到匹配的诊断记录。")
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['severity'].upper()}] {r['symptom']}")
                if r['cause']:
                    print(f"   原因: {r['cause']}")
                if r['solution']:
                    print(f"   解决方案: {r['solution'][:200]}")
                print(f"   来源: {r.get('source_file', r.get('source_page', '未知'))}")

    elif args.command == "list":
        results = db.list_all(severity=args.severity, status=args.status)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['severity']}] {r['symptom']} — {r['status']}")

    elif args.command == "stats":
        stats = db.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
