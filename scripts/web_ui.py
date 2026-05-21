#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
web_ui.py — LLM Wiki Web Interface

A Flask-based web UI for browsing, searching, and querying the wiki.

Usage:
    python3 scripts/web_ui.py [--port 5000] [--host 0.0.0.0]

Access:
    http://localhost:5000
"""

import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import WikiConfig
from vector_store import VectorStore
from embedding_client import EmbeddingClient
from scripts.query_engine import QueryEngine
from scripts.diagnosis_engine import DiagnosisDB, scan_sources

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
config = WikiConfig()
vector_store = VectorStore(config)
embedding_client = EmbeddingClient(config)
query_engine = QueryEngine(config)
diagnosis_db = DiagnosisDB(config)


# ── Helper functions ──────────────────────────────────────────────────────────

def read_file_safe(path: Path) -> str:
    """Read file content safely."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter."""
    return re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}
    fm_text = match.group(1)
    fm = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^(\w+):\s*(.+)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(',')]
            fm[key] = val
    return fm


def get_all_pages() -> list:
    """Get all wiki pages with metadata."""
    pages = []

    # Scan wiki directories
    for dir_name in ['infrastructure', 'sources', 'entities', 'concepts', 'queries', 'comparisons']:
        dir_path = config.wiki_dir / dir_name
        if dir_path.exists():
            for f in dir_path.glob('*.md'):
                if f.name in ('index.md', 'log.md', 'dashboard.md'):
                    continue
                content = read_file_safe(f)
                fm = parse_frontmatter(content)
                pages.append({
                    'path': str(f.relative_to(config.wiki_root)),
                    'name': f.stem.replace('-', ' ').title(),
                    'type': dir_name,
                    'category': fm.get('category', ''),
                    'tags': fm.get('tags', []),
                    'updated': fm.get('updated', ''),
                    'size': len(content),
                })

    # Scan diagnoses
    diag_dir = config.diagnoses_dir
    if diag_dir.exists():
        for f in diag_dir.glob('*.md'):
            content = read_file_safe(f)
            fm = parse_frontmatter(content)
            pages.append({
                'path': str(f.relative_to(config.wiki_root)),
                'name': f.stem.replace('-', ' ').title(),
                'type': 'diagnosis',
                'severity': fm.get('severity', 'medium'),
                'status': fm.get('status', 'historical'),
                'tags': fm.get('tags', []),
                'updated': fm.get('updated', ''),
                'size': len(content),
            })

    # Sort by updated date
    pages.sort(key=lambda x: x.get('updated', ''), reverse=True)
    return pages


def get_page_content(page_path: str) -> dict:
    """Get page content with metadata."""
    full_path = config.wiki_root / page_path
    if not full_path.exists():
        return {'error': '页面未找到'}

    content = read_file_safe(full_path)
    fm = parse_frontmatter(content)
    body = strip_frontmatter(content)

    return {
        'path': page_path,
        'name': full_path.stem.replace('-', ' ').title(),
        'type': fm.get('type', 'page'),
        'frontmatter': fm,
        'content': body,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Home page."""
    pages = get_all_pages()
    stats = {
        'total_pages': len(pages),
        'by_type': {},
        'total_vectors': vector_store.count(),
        'diagnoses': diagnosis_db.get_stats()['total'],
    }
    for p in pages:
        t = p['type']
        stats['by_type'][t] = stats['by_type'].get(t, 0) + 1

    return render_template('index.html', pages=pages, stats=stats)


@app.route('/page/<path:page_path>')
def page(page_path):
    """View a wiki page."""
    data = get_page_content(page_path)
    if 'error' in data:
        return render_template('error.html', error=data['error']), 404
    return render_template('page.html', **data)


@app.route('/search')
def search():
    """Search page."""
    query = request.args.get('q', '')
    results = []

    if query:
        # Vector search
        try:
            query_vector = embedding_client.embed_single(query)
            results = vector_store.search(query_vector, top_k=20)
        except Exception as e:
            return render_template('error.html', error=f'搜索出错: {e}'), 500

    return render_template('search.html', query=query, results=results)


@app.route('/query')
def query_page():
    """Intelligent Q&A page."""
    return render_template('query.html')


@app.route('/api/query', methods=['POST'])
def api_query():
    """API: Intelligent Q&A."""
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'error': '问题不能为空'}), 400

    try:
        result = query_engine.query(question, top_k=8)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """API: Vector search."""
    data = request.json
    query = data.get('query', '')
    top_k = data.get('top_k', 20)

    if not query:
        return jsonify({'error': '搜索关键词不能为空'}), 400

    try:
        query_vector = embedding_client.embed_single(query)
        results = vector_store.search(query_vector, top_k=top_k)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/diagnoses')
def diagnoses_page():
    """Diagnosis knowledge base page."""
    severity = request.args.get('severity', '')
    status = request.args.get('status', '')
    results = diagnosis_db.list_all(severity=severity, status=status, limit=100)
    stats = diagnosis_db.get_stats()
    return render_template('diagnoses.html', results=results, stats=stats)


@app.route('/api/diagnoses/search', methods=['POST'])
def api_diagnoses_search():
    """API: Search diagnoses."""
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({'error': '搜索关键词不能为空'}), 400

    results = diagnosis_db.search(query, limit=50)
    return jsonify(results)


@app.route('/topology')
def topology_page():
    """Topology graph page."""
    return render_template('topology.html')


@app.route('/api/stats')
def api_stats():
    """API: Wiki statistics."""
    pages = get_all_pages()
    stats = {
        'total_pages': len(pages),
        'by_type': {},
        'total_vectors': vector_store.count(),
        'vector_stats': vector_store.get_stats(),
        'diagnoses': diagnosis_db.get_stats(),
    }
    for p in pages:
        t = p['type']
        stats['by_type'][t] = stats['by_type'].get(t, 0) + 1
    return jsonify(stats)


@app.route('/topology.html')
def serve_topology():
    """Serve the generated topology HTML."""
    topology_path = config.wiki_dir / 'topology.html'
    if topology_path.exists():
        return send_from_directory(str(config.wiki_dir), 'topology.html')
    return 'Topology not generated. Run: ./wiki.sh graph', 404


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='LLM Wiki Web UI')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    print(f"🌐 LLM Wiki Web UI starting...")
    print(f"   Access: http://localhost:{args.port}")
    print(f"   Press Ctrl+C to stop")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
