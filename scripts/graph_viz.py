#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
graph_viz.py — Generate interactive D3 topology visualization from wiki infrastructure data.

Reads all infrastructure pages, extracts dependencies, and generates a standalone
HTML file with a force-directed graph.

Usage:
    python3 scripts/graph_viz.py [--output graph.html]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import WikiConfig


# ── Color palette by infrastructure type ──────────────────────────────────────
TYPE_COLORS = {
    "server": "#4CAF50",
    "switch": "#2196F3",
    "firewall": "#F44336",
    "database": "#FF9800",
    "service": "#9C27B0",
    "network": "#00BCD4",
    "storage": "#795548",
    "monitor": "#607D8B",
    "unknown": "#9E9E9E",
}

# ── Rel type → arrow style ────────────────────────────────────────────────────
REL_STYLES = {
    "depends_on": {"color": "#FF5722", "dash": "5,5"},
    "connected_to": {"color": "#2196F3", "dash": ""},
    "replicates_to": {"color": "#4CAF50", "dash": ""},
    "runs_on": {"color": "#9C27B0", "dash": "3,3"},
    "monitors": {"color": "#607D8B", "dash": "5,5"},
    "protects": {"color": "#F44336", "dash": ""},
    "backups_to": {"color": "#795548", "dash": "3,3"},
    "load_balances_to": {"color": "#00BCD4", "dash": ""},
}


def _parse_frontmatter(content: str) -> Dict:
    """Extract YAML frontmatter from markdown."""
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


def extract_infrastructure_nodes(config: WikiConfig) -> List[Dict]:
    """Scan all infrastructure pages and extract node data."""
    nodes = []
    infra_dir = config.infrastructure_dir

    if not infra_dir.exists():
        return nodes

    for file_path in infra_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(content)

        # Strip frontmatter for body parsing
        body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

        # Extract IP address
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', body)
        ip = ip_match.group(1) if ip_match else ""

        nodes.append({
            "id": file_path.stem,
            "name": file_path.stem.replace("-", " ").title(),
            "category": fm.get("category", "unknown"),
            "ip": ip,
            "file": str(file_path.relative_to(config.wiki_root)),
        })

    return nodes


def extract_infrastructure_edges(config: WikiConfig) -> List[Dict]:
    """Extract dependency relationships from infrastructure pages."""
    edges = []
    infra_dir = config.infrastructure_dir

    if not infra_dir.exists():
        return edges

    for file_path in infra_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

        source_id = file_path.stem

        # Extract wiki links in Dependencies/Depended By sections
        deps_section = re.search(r'## Dependencies\n(.*?)(?=## |\Z)', body, re.DOTALL)
        if deps_section:
            for link_match in re.finditer(r'\[\[wiki/infrastructure/([^\]|]+)', deps_section.group(1)):
                target_id = link_match.group(1)
                if target_id != source_id:
                    edges.append({
                        "source": source_id,
                        "target": target_id,
                        "relation_type": "depends_on",
                    })

        # Extract topology arrows: A → B
        for arrow_match in re.finditer(r'([A-Za-z][\w-]+)\s*→\s*([A-Za-z][\w-]+)', body):
            src = arrow_match.group(1)
            tgt = arrow_match.group(2)
            if src != tgt:
                edges.append({
                    "source": src,
                    "target": tgt,
                    "relation_type": "connected_to",
                })

        # Extract "运行在 X 上" pattern
        for run_match in re.finditer(r'([A-Za-z][\w-]+)\s*(?:运行在|runs\s+on)\s*([A-Za-z][\w-]+)', body):
            edges.append({
                "source": run_match.group(1),
                "target": run_match.group(2),
                "relation_type": "runs_on",
            })

    return edges


def generate_html(nodes: List[Dict], edges: List[Dict], output_path: Path):
    """Generate standalone HTML with D3 force-directed graph."""

    # Prepare D3 data
    node_data = []
    for n in nodes:
        color = TYPE_COLORS.get(n.get("category", "unknown"), TYPE_COLORS["unknown"])
        node_data.append({
            "id": n["id"],
            "name": n["name"],
            "category": n.get("category", "unknown"),
            "ip": n.get("ip", ""),
            "color": color,
        })

    edge_data = []
    for e in edges:
        style = REL_STYLES.get(e["relation_type"], {"color": "#999", "dash": ""})
        edge_data.append({
            "source": e["source"],
            "target": e["target"],
            "relation_type": e["relation_type"],
            "color": style["color"],
            "dash": style["dash"],
        })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Infrastructure Topology</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; }}
  #graph {{ width: 100vw; height: 100vh; }}
  #legend {{
    position: absolute; top: 20px; right: 20px;
    background: rgba(26, 26, 46, 0.95); padding: 16px;
    border-radius: 8px; font-size: 13px;
    border: 1px solid #333;
  }}
  #legend h3 {{ margin-bottom: 10px; color: #aaa; }}
  .legend-item {{ display: flex; align-items: center; margin: 4px 0; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
  #tooltip {{
    position: absolute; display: none;
    background: rgba(0,0,0,0.85); padding: 12px;
    border-radius: 6px; font-size: 13px;
    pointer-events: none; max-width: 250px;
    border: 1px solid #444;
  }}
  #tooltip .name {{ font-weight: bold; font-size: 15px; margin-bottom: 4px; }}
  #tooltip .ip {{ color: #aaa; }}
  #tooltip .cat {{ color: #888; font-size: 11px; }}
  #controls {{
    position: absolute; bottom: 20px; left: 20px;
    background: rgba(26, 26, 46, 0.95); padding: 12px;
    border-radius: 8px; font-size: 12px; color: #888;
    border: 1px solid #333;
  }}
</style>
</head>
<body>
<div id="graph"></div>

<div id="legend">
  <h3>Node Types</h3>
  {"".join(f'<div class="legend-item"><span class="legend-dot" style="background:{c}"></span>{t.replace("_", " ").title()}</div>' for t, c in TYPE_COLORS.items())}
</div>

<div id="tooltip">
  <div class="name"></div>
  <div class="ip"></div>
  <div class="cat"></div>
</div>

<div id="controls">
  Scroll to zoom · Drag to pan · Drag nodes to rearrange
</div>

<script>
const nodes = {json.dumps(node_data)};
const links = {json.dumps(edge_data)};

const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#graph")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

const g = svg.append("g");

// Zoom
const zoom = d3.zoom()
  .scaleExtent([0.1, 4])
  .on("zoom", (e) => g.attr("transform", e.transform));
svg.call(zoom);

// Arrow markers
const defs = svg.append("defs");
const relTypes = [...new Set(links.map(l => l.relation_type))];
relTypes.forEach(type => {{
  const marker = defs.append("marker")
    .attr("id", `arrow-${{type}}`)
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 28)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto");
  marker.append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", links.find(l => l.relation_type === type)?.color || "#999");
}});

// Force simulation
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(120))
  .force("charge", d3.forceManyBody().strength(-400))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(40));

// Links
const link = g.append("g")
  .selectAll("line")
  .data(links)
  .join("line")
  .attr("stroke", d => d.color)
  .attr("stroke-width", 2)
  .attr("stroke-dasharray", d => d.dash || "")
  .attr("marker-end", d => `url(#arrow-${{d.relation_type}})`);

// Link labels
const linkLabel = g.append("g")
  .selectAll("text")
  .data(links)
  .join("text")
  .attr("font-size", 10)
  .attr("fill", "#888")
  .text(d => d.relation_type.replace(/_/g, " "));

// Nodes
const node = g.append("g")
  .selectAll("g")
  .data(nodes)
  .join("g")
  .call(d3.drag()
    .on("start", (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on("drag", (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on("end", (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}));

node.append("circle")
  .attr("r", 22)
  .attr("fill", d => d.color)
  .attr("stroke", "#fff")
  .attr("stroke-width", 2)
  .attr("opacity", 0.9);

node.append("text")
  .attr("dy", 35)
  .attr("text-anchor", "middle")
  .attr("fill", "#ddd")
  .attr("font-size", 11)
  .text(d => d.name);

// Tooltip
const tooltip = d3.select("#tooltip");
node.on("mouseover", (e, d) => {{
  tooltip.style("display", "block")
    .select(".name").text(d.name);
  tooltip.select(".ip").text(d.ip || "");
  tooltip.select(".cat").text(d.category);
}})
.on("mousemove", (e) => {{
  tooltip.style("left", (e.pageX + 15) + "px")
    .style("top", (e.pageY - 10) + "px");
}})
.on("mouseout", () => tooltip.style("display", "none"));

// Tick
simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  linkLabel
    .attr("x", d => (d.source.x + d.target.x) / 2)
    .attr("y", d => (d.source.y + d.target.y) / 2 - 5);

  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

// Resize
window.addEventListener("resize", () => {{
  svg.attr("width", window.innerWidth).attr("height", window.innerHeight);
  simulation.force("center", d3.forceCenter(window.innerWidth / 2, window.innerHeight / 2));
  simulation.alpha(0.3).restart();
}});
</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate infrastructure topology graph")
    parser.add_argument("--output", "-o", default="wiki/topology.html",
                        help="Output HTML file path (default: wiki/topology.html)")
    args = parser.parse_args()

    config = WikiConfig()
    nodes = extract_infrastructure_nodes(config)
    edges = extract_infrastructure_edges(config)

    output_path = config.wiki_root / args.output
    generate_html(nodes, edges, output_path)

    print(f"✅ Topology graph generated: {output_path}")
    print(f"   Nodes: {len(nodes)}")
    print(f"   Edges: {len(edges)}")
    print(f"   Open in browser: file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
