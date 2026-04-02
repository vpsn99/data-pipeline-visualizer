# Data Pipeline Visualizer

A lightweight Python application to parse SQL/dbt-style models and visualize data pipeline lineage as a Directed Acyclic Graph (DAG).

---

## Overview

This project demonstrates how data pipelines can be:
- Parsed from SQL models
- Represented as a DAG
- Analyzed for dependencies and execution order

It is designed as a **portfolio project** for Data Engineer / Data Architect roles.

---

## Features (V1)

- Parse SQL files from a folder
- Extract table/model dependencies
- Build a DAG using NetworkX
- Classify nodes:
  - Sources
  - Intermediate models
  - Final outputs
- Detect cycles in pipelines
- Generate topological execution order

---

## Project Structure

```
app/
  parser.py            # SQL parsing & dependency extraction
  graph_builder.py     # DAG construction & analysis
  main.py              # CLI entry point

tests/
  test_parser.py
  test_graph_builder.py

models/                # Sample SQL models
```

---

## Installation

```bash
git clone <your-repo-url>
cd data-pipeline-visualizer

python -m venv .venv
.venv\Scripts\activate   # Windows

pip install -r requirements.txt
pip install -e .
```

---

## Usage

```bash
python -m app.main models
```

### Example Output

```
=== Dependency Map ===
{
  "fct_sales": ["stg_orders", "stg_customers"],
  "stg_orders": ["raw.orders"],
  "stg_customers": ["raw.customers"]
}

=== Graph Summary ===
{
  "num_nodes": 5,
  "num_edges": 4,
  "is_dag": true,
  "sources": ["raw.orders", "raw.customers"],
  "intermediates": ["stg_orders", "stg_customers"],
  "finals": ["fct_sales"]
}
```

---
## Sample DAG Output

![Pipeline DAG](/docs/pipeline_dag.png)
---

## Sample Explanation

Pipeline Summary
This pipeline contains 5 nodes...

Node Explanations

stg_orders is an intermediate model...


## Sample Insights
Pipeline Insights

The pipeline depth is 2 step(s)
fct_sales has 2 upstream dependencies...

## Tech Stack

- Python 3.11+
- networkx
- pytest
- ruff

---

## Design Principles

- Keep parsing **simple and heuristic-based**
- Focus on **clarity over completeness**
- Build a **modular architecture**
- Enable **incremental enhancements**

---

##  Roadmap

### V1 (Current)
- [x] SQL parsing
- [x] Dependency extraction
- [x] DAG construction
- [x] Node classification
- [x] Cycle detection

### Next Steps
- [ ] DAG visualization (Graphviz)
- [ ] Explanation engine (plain English)
- [ ] Pipeline insights (complexity, bottlenecks)
- [ ] Streamlit UI

---

## Why This Project?

This project showcases:
- Data lineage understanding
- Graph-based thinking
- SQL parsing logic
- Clean modular Python design

Ideal for demonstrating real-world data engineering concepts in interviews.

---

## Author
Virendra Pratap Singh
https://www.linkedin.com/in/virendra-pratap-singh-iitg/
### NVA Dataworks
Built as a portfolio project to demonstrate data pipeline architecture and visualization concepts.
