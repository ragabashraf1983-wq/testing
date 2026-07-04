"""
v5 Process Graph Tracker — Real-time network visualization of agent workflow.
Exports interactive D3.js HTML for user monitoring.
"""

import json
import time
from typing import Dict, Any, List, Optional

import networkx as nx


class GraphTracker:
    """Tracks the research workflow as a directed graph."""

    AGENT_COLORS = {
        "Orchestrator": "#e74c3c",
        "LinguistExpert": "#3498db",
        "MathematicianExpert": "#2ecc71",
        "PhysicistExpert": "#f39c12",
        "StatisticianExpert": "#9b59b6",
        "MethodologistExpert": "#1abc9c",
        "LogisticianExpert": "#34495e",
        "EpistemologistExpert": "#e67e22",
        "DraftingAgent": "#2980b9",
        "ExperimentAgent": "#c0392b",
        "EditorAgent": "#8e44ad",
        "MethodologyReviewer": "#16a085",
        "LiteratureReviewer": "#27ae60",
        "ResultsReviewer": "#d35400",
        "ImpactReviewer": "#2c3e50",
        "NoveltyReviewer": "#f1c40f",
        "ConflictResolutionAgent": "#e91e63",
        "LiteratureScout": "#00cec9",
        "GapAnalyst": "#fd79a8",
        "Methodologist": "#6c5ce7",
        "AcademicAuthor": "#e17055",
    }

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.graph = nx.DiGraph()
        self.node_counter = 0
        self.active_nodes: set = set()

    def add_event(
        self,
        agent: str,
        role: str,
        action: str,
        state: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        status: str = "completed",
    ) -> str:
        self.node_counter += 1
        node_id = f"{agent}_{self.node_counter}_{int(time.time() * 1000)}"
        self.graph.add_node(
            node_id,
            label=action,
            agent=agent,
            role=role,
            state=state,
            timestamp=time.time(),
            color=self.AGENT_COLORS.get(agent, "#95a5a6"),
            metadata=metadata or {},
            status=status,
        )
        if parent_id:
            self.graph.add_edge(parent_id, node_id, relation="triggers")
        if status == "running":
            self.active_nodes.add(node_id)
        elif status in ("completed", "failed") and node_id in self.active_nodes:
            self.active_nodes.discard(node_id)
            self.graph.nodes[node_id]["status"] = status
        return node_id

    def update_status(self, node_id: str, status: str):
        if node_id in self.graph:
            self.graph.nodes[node_id]["status"] = status
            if status == "running":
                self.active_nodes.add(node_id)
            else:
                self.active_nodes.discard(node_id)

    def to_json(self) -> str:
        data = {
            "project_id": self.project_id,
            "generated_at": time.time(),
            "nodes": [],
            "edges": [],
            "active_nodes": list(self.active_nodes),
        }
        for n, attr in self.graph.nodes(data=True):
            data["nodes"].append({
                "id": n,
                "label": attr.get("label"),
                "agent": attr.get("agent"),
                "role": attr.get("role"),
                "state": attr.get("state"),
                "timestamp": attr.get("timestamp"),
                "color": attr.get("color"),
                "status": attr.get("status"),
                "metadata": attr.get("metadata"),
            })
        for u, v, attr in self.graph.edges(data=True):
            data["edges"].append({
                "source": u,
                "target": v,
                "relation": attr.get("relation"),
            })
        return json.dumps(data, indent=2)

    def export_html(self, filepath: str):
        """Export an interactive D3.js HTML graph."""
        graph_json = self.to_json()
        # Use string replacement to avoid f-string conflicts with JS template literals
        html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Research Agent Process Graph</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #1a1a2e; color: #eee; overflow: hidden; }
#graph { width: 100vw; height: 100vh; }
.tooltip { position: absolute; background: rgba(0,0,0,0.85); padding: 10px; border-radius: 6px; pointer-events: none; font-size: 12px; border: 1px solid #444; max-width: 300px; }
.legend { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); padding: 12px; border-radius: 8px; font-size: 12px; }
.legend-item { display: flex; align-items: center; margin: 4px 0; }
.legend-color { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
.status-running { animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { opacity: 1; r: 8; } 50% { opacity: 0.5; r: 12; } 100% { opacity: 1; r: 8; } }
</style>
</head>
<body>
<div id="tooltip" class="tooltip" style="display:none"></div>
<div class="legend" id="legend"></div>
<svg id="graph"></svg>
<script>
const graphData = __GRAPH_DATA__;
const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#graph")
  .attr("width", width)
  .attr("height", height)
  .call(d3.zoom().on("zoom", (event) => g.attr("transform", event.transform)))
  .append("g");

const g = svg.append("g");

const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(30));

const link = g.append("g")
  .selectAll("line")
  .data(graphData.edges)
  .join("line")
  .attr("stroke", "#555")
  .attr("stroke-opacity", 0.6)
  .attr("stroke-width", 1.5);

const node = g.append("g")
  .selectAll("g")
  .data(graphData.nodes)
  .join("g")
  .call(d3.drag()
    .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
    .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

node.append("circle")
  .attr("r", d => d.status === "running" ? 10 : 7)
  .attr("fill", d => d.color)
  .attr("class", d => d.status === "running" ? "status-running" : "")
  .attr("stroke", "#fff")
  .attr("stroke-width", 1.5);

node.append("text")
  .text(d => d.agent)
  .attr("x", 12)
  .attr("y", 4)
  .attr("font-size", "10px")
  .attr("fill", "#ddd");

const tooltip = d3.select("#tooltip");
node.on("mouseover", (event, d) => {
  tooltip.style("display", "block")
    .html('<strong>' + d.agent + '</strong><br>Role: ' + d.role + '<br>Action: ' + d.label + '<br>State: ' + d.state + '<br>Status: ' + d.status + '<br>' + new Date(d.timestamp*1000).toLocaleTimeString());
})
.on("mousemove", (event) => {
  tooltip.style("left", (event.pageX + 10) + "px").style("top", (event.pageY + 10) + "px");
})
.on("mouseout", () => tooltip.style("display", "none"));

simulation.on("tick", () => {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
  node.attr("transform", d => 'translate(' + d.x + ',' + d.y + ')');
});

// Build legend
const legend = d3.select("#legend");
const agents = [...new Set(graphData.nodes.map(d => d.agent))];
agents.forEach(agent => {
  const color = graphData.nodes.find(n => n.agent === agent)?.color || "#999";
  const item = legend.append("div").attr("class", "legend-item");
  item.append("div").attr("class", "legend-color").style("background", color);
  item.append("span").text(agent);
});
</script>
</body>
</html>
"""
        html = html_template.replace("__GRAPH_DATA__", graph_json)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
