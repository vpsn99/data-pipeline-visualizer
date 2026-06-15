from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import streamlit as st

from app.insights import explain_insights, summarize_insights

st.set_page_config(
    page_title="Data Pipeline Visualizer",
    layout="wide",
)


CATALOG_FILE = Path("output/model_catalog.json")
DAG_FILE = Path("output/pipeline_dag.png")
REPORT_FILE = Path("output/pipeline_report.md")
GRAPH_FILE = Path("output/graph_data.json")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def build_graph_from_export(graph_data: dict[str, Any]) -> nx.DiGraph:
    """
    Rebuild a NetworkX graph from exported graph_data.json.
    """
    graph = nx.DiGraph()

    for node in graph_data.get("nodes", []):
        node_id = node["id"]
        attrs = {key: value for key, value in node.items() if key != "id"}
        graph.add_node(node_id, **attrs)

    for edge in graph_data.get("edges", []):
        graph.add_edge(edge["source"], edge["target"])

    return graph


def summarize_layers(catalog: dict[str, dict[str, Any]]) -> dict[str, int]:
    counter = Counter()

    for model in catalog.values():
        counter[model.get("layer", "other")] += 1

    return dict(counter)


def summarize_complexity(catalog: dict[str, dict[str, Any]]) -> dict[str, int]:
    counter = Counter()

    for model in catalog.values():
        counter[model.get("complexity_level", "unknown")] += 1

    return dict(counter)


def list_text(values: list[str]) -> str:
    if not values:
        return "None"
    return "\n".join(f"- {value}" for value in values)


st.title("Data Pipeline Visualizer")

if not CATALOG_FILE.exists():
    st.error("model_catalog.json not found. Run the pipeline first.")
    st.code("python -m app.main models --parser auto", language="powershell")
    st.stop()

catalog = load_json(CATALOG_FILE)

graph: nx.DiGraph | None = None

if GRAPH_FILE.exists():
    graph_data = load_json(GRAPH_FILE)
    graph = build_graph_from_export(graph_data)

st.header("Pipeline Overview")

total_models = len(catalog)
source_models = sum(1 for model in catalog.values() if model.get("node_type") == "source")
final_models = sum(1 for model in catalog.values() if model.get("node_type") == "final")
fact_models = sum(1 for model in catalog.values() if model.get("layer") == "fact")
dimension_models = sum(1 for model in catalog.values() if model.get("layer") == "dimension")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Models", total_models)
col2.metric("Sources", source_models)
col3.metric("Final Outputs", final_models)
col4.metric("Facts", fact_models)
col5.metric("Dimensions", dimension_models)

st.divider()

st.header("Layer Summary")

layer_summary = summarize_layers(catalog)
layer_rows = [
    {"Layer": layer.title(), "Count": count} for layer, count in sorted(layer_summary.items())
]

if layer_rows:
    st.dataframe(
        pd.DataFrame(layer_rows),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No layer information available.")

st.header("Complexity Summary")

complexity_summary = summarize_complexity(catalog)
complexity_rows = [
    {"Complexity": level.title(), "Count": count}
    for level, count in sorted(complexity_summary.items())
]

if complexity_rows:
    st.dataframe(
        pd.DataFrame(complexity_rows),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No complexity information available.")

st.divider()

st.header("Pipeline DAG")

if DAG_FILE.exists():
    st.image(str(DAG_FILE), use_container_width=True)
else:
    st.warning("pipeline_dag.png not found. Run the pipeline to generate the DAG image.")

st.divider()

st.header("Pipeline Insights")

if graph is None:
    st.warning("graph_data.json not found. Run the pipeline to generate graph insights.")
else:
    insights = summarize_insights(graph)

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric("Pipeline Depth", insights.get("pipeline_depth", 0))
    metric_col2.metric(
        "High Fan-In Nodes",
        len(insights.get("high_fan_in_nodes", [])),
    )
    metric_col3.metric(
        "High Fan-Out Nodes",
        len(insights.get("high_fan_out_nodes", [])),
    )

    longest_path = insights.get("longest_path", [])
    if longest_path:
        st.markdown("**Longest Lineage Path**")
        st.code(" → ".join(longest_path), language="text")

    with st.expander("Insight Narration", expanded=True):
        st.text(explain_insights(graph))

    high_fan_in_nodes = insights.get("high_fan_in_nodes", [])
    if high_fan_in_nodes:
        st.markdown("**High Fan-In Nodes**")
        st.dataframe(
            pd.DataFrame(high_fan_in_nodes),
            use_container_width=True,
            hide_index=True,
        )

    high_fan_out_nodes = insights.get("high_fan_out_nodes", [])
    if high_fan_out_nodes:
        st.markdown("**High Fan-Out Nodes**")
        st.dataframe(
            pd.DataFrame(high_fan_out_nodes),
            use_container_width=True,
            hide_index=True,
        )

st.divider()

st.header("Model Explorer")

selected_model = st.selectbox(
    "Select Model",
    sorted(catalog.keys()),
)

model = catalog[selected_model]

left, right = st.columns(2)

with left:
    st.subheader(selected_model)

    st.write(f"**Node Type:** {model.get('node_type', 'unknown')}")

    layer = model.get("layer", "other")
    st.info(f"Layer: {layer.title()}")

    level = model.get("complexity_level", "unknown")

    if level == "high":
        st.error(f"Complexity: {level.title()}")
    elif level == "medium":
        st.warning(f"Complexity: {level.title()}")
    else:
        st.success(f"Complexity: {level.title()}")

    st.write(f"**Complexity Score:** {model.get('complexity_score', 0)}")

    pattern = model.get("dominant_pattern")
    if pattern:
        st.caption(f"Transformation Pattern: {pattern.replace('_', ' ').title()}")

with right:
    st.subheader("Parser Diagnostics")

    parser_used = model.get("parser_used", "N/A")
    parse_status = model.get("parse_status", "N/A")

    st.write(f"**Parser Used:** {parser_used}")

    if parse_status == "success":
        st.success(f"Parse Status: {parse_status.title()}")
    elif parse_status == "fallback":
        st.warning(f"Parse Status: {parse_status.title()}")
    else:
        st.error(f"Parse Status: {parse_status.title()}")

    parse_error = model.get("parse_error")
    if parse_error:
        st.warning(parse_error)
    else:
        st.success("No parser errors.")

st.subheader("Lineage")

lineage_left, lineage_right = st.columns(2)

with lineage_left:
    st.markdown("**Dependencies**")
    st.markdown(list_text(model.get("dependencies", [])))

with lineage_right:
    st.markdown("**Downstream Models**")
    st.markdown(list_text(model.get("downstream_models", [])))

st.subheader("SQL Intelligence")

sql_col1, sql_col2 = st.columns(2)

with sql_col1:
    st.markdown("**Join Details**")
    st.write(f"Join Count: {model.get('join_count', 0)}")
    st.write(f"Join Types: {', '.join(model.get('join_types', [])) or 'None'}")
    st.markdown("Join Keys:")
    st.markdown(list_text(model.get("join_keys", [])))

with sql_col2:
    st.markdown("**Aggregation / Filtering**")
    st.write(f"Aggregate Functions: {', '.join(model.get('aggregate_functions', [])) or 'None'}")
    st.markdown("Group By Columns:")
    st.markdown(list_text(model.get("group_by_columns", [])))

    where_clause = model.get("where_clause")
    st.write(f"Where Clause: {where_clause or 'None'}")

selected_columns = model.get("selected_columns", [])
if selected_columns:
    with st.expander("Selected Columns"):
        st.markdown(list_text(selected_columns))

with st.expander("Raw Model Metadata"):
    st.json(model)

st.divider()

st.header("Report Download")

if REPORT_FILE.exists():
    report_text = REPORT_FILE.read_text(encoding="utf-8")

    st.download_button(
        label="Download Markdown Report",
        data=report_text,
        file_name="pipeline_report.md",
        mime="text/markdown",
    )
else:
    st.warning("pipeline_report.md not found.")
