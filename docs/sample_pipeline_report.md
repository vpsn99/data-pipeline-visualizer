# Data Pipeline Report

## Graph Summary

- **Nodes:** 6
- **Edges:** 5
- **Is DAG:** True
- **Sources:** raw.customers, raw.orders
- **Intermediates:** int_customer_orders, stg_customers, stg_orders
- **Finals:** fct_sales

## Topological Order

```text
raw.customers
raw.orders
stg_customers
stg_orders
int_customer_orders
fct_sales
```

## Pipeline DAG

![Pipeline DAG](output/pipeline_dag.png)

## Explanation

```text
Pipeline Summary
This pipeline contains 6 nodes and 5 dependency edges. It starts from 2 source nodes: raw.customers and raw.orders. It includes 3 intermediate models: int_customer_orders, stg_customers, and stg_orders. It produces 1 final outputs: fct_sales.

Node Explanations
- fct_sales is a fact model built from int_customer_orders. It is a medium complexity model. It aggregates data at the level of customer_name. It is primarily an aggregation model, selects customer_name, SUM(amount) AS total_amount, COUNT(*) AS order_count, aggregates by customer_name, uses aggregate functions: count, sum, applies having logic using SUM(amount) > 100.
- int_customer_orders is an intermediate model built from stg_customers and stg_orders and used by fct_sales. It is a medium complexity model. It enriches data by combining stg_customers, stg_orders. It is primarily an enrichment model, selects c.customer_id, c.customer_name, o.order_id ..., uses aliases c=stg_customers AS c, o=stg_orders AS o, uses left join logic, joins on c.customer_id = o.customer_id, filters rows using o.amount > 0.
- raw.customers is a source table that feeds into stg_customers.
- raw.orders is a source table that feeds into stg_orders.
- stg_customers is an intermediate model built from raw.customers and used by int_customer_orders. It is a low complexity model. It prepares and standardizes source data. It is primarily a staging model, selects customer_id, customer_name, region.
- stg_orders is an intermediate model built from raw.orders and used by int_customer_orders. It is a low complexity model. It prepares and standardizes source data. It is primarily a staging model, selects order_id, customer_id, order_date ....

Example Lineage Paths
- Lineage path: raw.customers -> stg_customers -> int_customer_orders -> fct_sales
- Lineage path: raw.orders -> stg_orders -> int_customer_orders -> fct_sales
```

## Parser Diagnostics

```json
{
  "fct_sales": {
    "parser_used": "sqlglot",
    "parse_status": "success",
    "parse_error": null
  },
  "int_customer_orders": {
    "parser_used": "sqlglot",
    "parse_status": "success",
    "parse_error": null
  },
  "stg_customers": {
    "parser_used": "sqlglot",
    "parse_status": "success",
    "parse_error": null
  },
  "stg_orders": {
    "parser_used": "sqlglot",
    "parse_status": "success",
    "parse_error": null
  }
}
```

## Model Layers

```json
{
  "fct_sales": "fact",
  "int_customer_orders": "intermediate",
  "stg_customers": "staging",
  "stg_orders": "staging"
}
```

## Layer Summary

```json
{
  "fact": 1,
  "intermediate": 1,
  "staging": 2
}
```

## Model Complexity

```json
{
  "fct_sales": {
    "score": 3,
    "level": "medium"
  },
  "int_customer_orders": {
    "score": 4,
    "level": "medium"
  },
  "stg_customers": {
    "score": 1,
    "level": "low"
  },
  "stg_orders": {
    "score": 1,
    "level": "low"
  }
}
```

## Insights

```text
Pipeline Insights
- The pipeline depth is 3 step(s).
- One of the longest lineage paths is: raw.customers -> stg_customers -> int_customer_orders -> fct_sales.
- int_customer_orders has 2 upstream dependencies, which makes it a relatively complex transformation node.
- No nodes have high fan-out in the current pipeline.
- The deepest node is fct_sales at depth 3.
```

## Structured Insights

```json
{
  "pipeline_depth": 3,
  "longest_path": [
    "raw.customers",
    "stg_customers",
    "int_customer_orders",
    "fct_sales"
  ],
  "high_fan_in_nodes": [
    {
      "node": "int_customer_orders",
      "fan_in": 2,
      "upstreams": [
        "stg_customers",
        "stg_orders"
      ],
      "node_type": "intermediate"
    }
  ],
  "high_fan_out_nodes": [],
  "isolated_nodes": [],
  "deepest_nodes": [
    {
      "node": "fct_sales",
      "depth": 3,
      "node_type": "final"
    },
    {
      "node": "int_customer_orders",
      "depth": 2,
      "node_type": "intermediate"
    },
    {
      "node": "stg_customers",
      "depth": 1,
      "node_type": "intermediate"
    },
    {
      "node": "stg_orders",
      "depth": 1,
      "node_type": "intermediate"
    },
    {
      "node": "raw.customers",
      "depth": 0,
      "node_type": "source"
    }
  ]
}
```
