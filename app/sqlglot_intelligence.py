from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp


@dataclass
class SqlglotExtraction:
    selected_columns: list[str]
    table_aliases: dict[str, str]
    join_types: list[str]
    join_conditions: list[str]
    join_keys: list[str]
    group_by_columns: list[str]
    where_clause: str | None
    having_clause: str | None
    aggregate_functions: list[str]
    window_functions: list[str]
    parse_error: str | None = None


def _safe_sql(node: exp.Expression | None) -> str | None:
    return node.sql() if node is not None else None


def _extract_selected_columns(tree: exp.Expression) -> list[str]:
    if not isinstance(tree, exp.Select):
        select = tree.find(exp.Select)
    else:
        select = tree

    if not select:
        return []

    return [projection.sql() for projection in select.expressions]


def _extract_table_aliases(tree: exp.Expression) -> dict[str, str]:
    aliases: dict[str, str] = {}

    for table in tree.find_all(exp.Table):
        alias = table.alias
        if alias:
            aliases[alias] = table.sql()

    return aliases


def _extract_join_info(tree: exp.Expression) -> tuple[list[str], list[str], list[str]]:
    join_types: list[str] = []
    join_conditions: list[str] = []
    join_keys: list[str] = []

    for join in tree.find_all(exp.Join):
        side = (join.args.get("side") or "").lower()
        kind = (join.args.get("kind") or "").lower()

        if side and kind:
            join_type = f"{side} {kind}".strip()
        else:
            join_type = side or kind or "join"

        join_types.append(join_type)

        on_expr = join.args.get("on")
        if on_expr is not None:
            join_conditions.append(on_expr.sql())

            for eq in on_expr.find_all(exp.EQ):
                left = eq.this.sql() if eq.this is not None else None
                right = eq.expression.sql() if eq.expression is not None else None
                if left and right:
                    join_keys.append(f"{left} = {right}")

    return sorted(set(join_types)), join_conditions, sorted(set(join_keys))


def _extract_group_by_columns(tree: exp.Expression) -> list[str]:
    group = tree.find(exp.Group)
    if not group:
        return []

    return [expr.sql() for expr in group.expressions]


def _extract_where_clause(tree: exp.Expression) -> str | None:
    where = tree.find(exp.Where)
    return _safe_sql(where.this if where else None)


def _extract_having_clause(tree: exp.Expression) -> str | None:
    having = tree.find(exp.Having)
    return _safe_sql(having.this if having else None)


def _extract_aggregate_functions(tree: exp.Expression) -> list[str]:
    aggs: set[str] = set()

    for node in tree.walk():
        if isinstance(node, exp.AggFunc):
            aggs.add(node.key.lower())

    return sorted(aggs)


def _extract_window_functions(tree: exp.Expression) -> list[str]:
    wins: set[str] = set()

    for window in tree.find_all(exp.Window):
        func = window.this
        if func is not None:
            wins.add(func.key.lower())

    return sorted(wins)


def analyze_with_sqlglot(sql: str, dialect: str | None = None) -> SqlglotExtraction:
    try:
        tree = sqlglot.parse_one(sql, dialect=dialect)
    except Exception as exc:
        return SqlglotExtraction(
            selected_columns=[],
            table_aliases={},
            join_types=[],
            join_conditions=[],
            join_keys=[],
            group_by_columns=[],
            where_clause=None,
            having_clause=None,
            aggregate_functions=[],
            window_functions=[],
            parse_error=str(exc),
        )

    return SqlglotExtraction(
        selected_columns=_extract_selected_columns(tree),
        table_aliases=_extract_table_aliases(tree),
        join_types=_extract_join_info(tree)[0],
        join_conditions=_extract_join_info(tree)[1],
        join_keys=_extract_join_info(tree)[2],
        group_by_columns=_extract_group_by_columns(tree),
        where_clause=_extract_where_clause(tree),
        having_clause=_extract_having_clause(tree),
        aggregate_functions=_extract_aggregate_functions(tree),
        window_functions=_extract_window_functions(tree),
        parse_error=None,
    )
