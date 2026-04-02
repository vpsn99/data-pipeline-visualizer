from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.parser import extract_dependencies, remove_sql_comments

JOIN_TYPE_PATTERNS = {
    "inner": re.compile(r"\binner\s+join\b", re.IGNORECASE),
    "left": re.compile(r"\bleft(?:\s+outer)?\s+join\b", re.IGNORECASE),
    "right": re.compile(r"\bright(?:\s+outer)?\s+join\b", re.IGNORECASE),
    "full": re.compile(r"\bfull(?:\s+outer)?\s+join\b", re.IGNORECASE),
    "cross": re.compile(r"\bcross\s+join\b", re.IGNORECASE),
    "join": re.compile(r"\bjoin\b", re.IGNORECASE),
}

AGGREGATE_FUNCTION_PATTERN = re.compile(
    r"\b(sum|count|avg|min|max)\s*\(",
    re.IGNORECASE,
)

WINDOW_FUNCTION_PATTERN = re.compile(
    r"\b(row_number|rank|dense_rank|lag|lead|first_value|last_value)\s*\(",
    re.IGNORECASE,
)


@dataclass
class SqlSemantics:
    model_name: str
    source_tables: list[str] = field(default_factory=list)

    has_join: bool = False
    join_count: int = 0
    join_types: list[str] = field(default_factory=list)
    join_conditions: list[str] = field(default_factory=list)
    join_keys: list[str] = field(default_factory=list)

    has_where: bool = False
    where_clause: str | None = None

    has_group_by: bool = False
    group_by_columns: list[str] = field(default_factory=list)

    has_having: bool = False
    having_clause: str | None = None

    has_order_by: bool = False
    has_distinct: bool = False

    cte_count: int = 0
    has_subquery: bool = False
    has_union: bool = False
    has_window_functions: bool = False
    window_functions: list[str] = field(default_factory=list)

    aggregate_functions: list[str] = field(default_factory=list)
    selected_columns: list[str] = field(default_factory=list)
    table_aliases: dict[str, str] = field(default_factory=dict)

    inferred_patterns: list[str] = field(default_factory=list)
    dominant_pattern: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def count_ctes(sql: str) -> int:
    matches = re.findall(r"\bwith\s+[a-zA-Z_][a-zA-Z0-9_]*\s+as\s*\(", sql, re.IGNORECASE)
    additional = re.findall(r",\s*[a-zA-Z_][a-zA-Z0-9_]*\s+as\s*\(", sql, re.IGNORECASE)
    return len(matches) + len(additional)


def detect_subquery(sql: str) -> bool:
    return bool(re.search(r"\(\s*select\b", sql, re.IGNORECASE))


def detect_window_functions(sql: str) -> bool:
    return bool(re.search(r"\bover\s*\(", sql, re.IGNORECASE))


def detect_join_types(sql: str) -> list[str]:
    detected: list[str] = []

    for join_type, pattern in JOIN_TYPE_PATTERNS.items():
        if join_type == "join":
            continue
        if pattern.search(sql):
            detected.append(join_type)

    if not detected and JOIN_TYPE_PATTERNS["join"].search(sql):
        detected.append("join")

    return sorted(set(detected))


def extract_join_conditions(sql: str) -> list[str]:
    """
    Heuristically extract ON conditions from JOIN clauses.
    """
    pattern = re.compile(
        r"\bjoin\b.*?\bon\b(.*?)(?=\bjoin\b|\bwhere\b|\bgroup\s+by\b|\bhaving\b|\border\s+by\b|$)",
        re.IGNORECASE | re.DOTALL,
    )
    matches = pattern.findall(sql)

    conditions: list[str] = []
    for match in matches:
        cleaned = " ".join(match.split()).strip(" ,;")
        if cleaned:
            conditions.append(cleaned)

    return conditions


def extract_join_keys(join_conditions: list[str]) -> list[str]:
    """
    Extract simple equality join keys from join conditions.
    """
    keys: list[str] = []

    for condition in join_conditions:
        matches = re.findall(
            r"([a-zA-Z_][a-zA-Z0-9_\.]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_\.]*)",
            condition,
            re.IGNORECASE,
        )
        for left, right in matches:
            keys.append(f"{left} = {right}")

    return sorted(set(keys))


def extract_clause_body(sql: str, clause_name: str, stop_clauses: list[str]) -> str | None:
    """
    Extract a clause body, such as WHERE ... or HAVING ...
    """
    stop_pattern = "|".join(stop_clauses)
    pattern = re.compile(
        rf"\b{clause_name}\b(.*?)(?={stop_pattern}|$)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(sql)
    if not match:
        return None

    clause = " ".join(match.group(1).split()).strip(" ,;")
    return clause or None


def extract_group_by_columns(sql: str) -> list[str]:
    """
    Heuristically extract GROUP BY column expressions.
    """
    clause = extract_clause_body(
        sql,
        clause_name="group by",
        stop_clauses=[r"\bhaving\b", r"\border\s+by\b"],
    )
    if not clause:
        return []

    return [part.strip() for part in clause.split(",") if part.strip()]


def extract_aggregate_functions(sql: str) -> list[str]:
    matches = AGGREGATE_FUNCTION_PATTERN.findall(sql)
    return sorted({match.lower() for match in matches})


def extract_window_functions(sql: str) -> list[str]:
    matches = WINDOW_FUNCTION_PATTERN.findall(sql)
    return sorted({match.lower() for match in matches})


def extract_select_clause(sql: str) -> str | None:
    """
    Extract the text between SELECT and FROM.
    Heuristic only; good enough for Phase 3.
    """
    pattern = re.compile(
        r"\bselect\b\s+(.*?)\s+\bfrom\b",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(sql)
    if not match:
        return None

    return " ".join(match.group(1).split()).strip()


def split_select_expressions(select_clause: str) -> list[str]:
    """
    Split SELECT expressions by commas, ignoring commas inside parentheses.
    """
    expressions: list[str] = []
    current: list[str] = []
    depth = 0

    for char in select_clause:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(depth - 1, 0)

        if char == "," and depth == 0:
            expr = "".join(current).strip()
            if expr:
                expressions.append(expr)
            current = []
        else:
            current.append(char)

    tail = "".join(current).strip()
    if tail:
        expressions.append(tail)

    return expressions


def extract_selected_columns(sql: str) -> list[str]:
    """
    Extract top-level SELECT expressions.
    """
    select_clause = extract_select_clause(sql)
    if not select_clause:
        return []

    return split_select_expressions(select_clause)


def extract_table_aliases(sql: str) -> dict[str, str]:
    """
    Extract simple table alias mappings from FROM/JOIN clauses.
    Examples:
      FROM orders o
      JOIN customers AS c
    """
    pattern = re.compile(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+(?:as\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\b",
        re.IGNORECASE,
    )
    matches = pattern.findall(sql)

    aliases: dict[str, str] = {}
    reserved = {"where", "group", "order", "having", "join", "on"}

    for table_name, alias in matches:
        if alias.lower() in reserved:
            continue
        aliases[alias] = table_name

    return aliases


def infer_patterns(semantics: SqlSemantics) -> list[str]:
    patterns: list[str] = []

    if semantics.has_group_by or semantics.aggregate_functions:
        patterns.append("aggregation")

    if semantics.has_join:
        patterns.append("join_enrichment")

    if semantics.has_where:
        patterns.append("filtering")

    if semantics.has_distinct:
        patterns.append("deduplication_or_distinct_selection")

    if semantics.has_union:
        patterns.append("union_combination")

    if semantics.has_window_functions:
        patterns.append("windowed_calculation")

    if not patterns and len(semantics.source_tables) == 1:
        patterns.append("simple_projection_or_staging")

    return patterns


def infer_dominant_pattern(semantics: SqlSemantics) -> str | None:
    if semantics.has_window_functions:
        return "windowed"
    if semantics.has_group_by or semantics.aggregate_functions:
        return "aggregation"
    if semantics.has_join:
        return "enrichment"
    if semantics.has_union:
        return "unioned"
    if semantics.has_distinct:
        return "deduplicated"
    if semantics.has_where:
        return "filtered"
    if len(semantics.source_tables) == 1:
        return "staging"
    return None


def analyze_sql(model_name: str, sql: str) -> SqlSemantics:
    cleaned_sql = remove_sql_comments(sql)

    join_types = detect_join_types(cleaned_sql)
    dependencies = extract_dependencies(cleaned_sql)
    where_clause = extract_clause_body(
        cleaned_sql,
        clause_name="where",
        stop_clauses=[r"\bgroup\s+by\b", r"\bhaving\b", r"\border\s+by\b"],
    )
    having_clause = extract_clause_body(
        cleaned_sql,
        clause_name="having",
        stop_clauses=[r"\border\s+by\b"],
    )
    group_by_columns = extract_group_by_columns(cleaned_sql)
    aggregate_functions = extract_aggregate_functions(cleaned_sql)
    join_conditions = extract_join_conditions(cleaned_sql)
    join_keys = extract_join_keys(join_conditions)
    selected_columns = extract_selected_columns(cleaned_sql)
    table_aliases = extract_table_aliases(cleaned_sql)
    window_functions = extract_window_functions(cleaned_sql)

    semantics = SqlSemantics(
        model_name=model_name,
        source_tables=dependencies,
        has_join=bool(re.search(r"\bjoin\b", cleaned_sql, re.IGNORECASE)),
        join_count=len(re.findall(r"\bjoin\b", cleaned_sql, re.IGNORECASE)),
        join_types=join_types,
        join_conditions=join_conditions,
        join_keys=join_keys,
        has_where=where_clause is not None,
        where_clause=where_clause,
        has_group_by=bool(re.search(r"\bgroup\s+by\b", cleaned_sql, re.IGNORECASE)),
        group_by_columns=group_by_columns,
        has_having=having_clause is not None,
        having_clause=having_clause,
        has_order_by=bool(re.search(r"\border\s+by\b", cleaned_sql, re.IGNORECASE)),
        has_distinct=bool(re.search(r"\bselect\s+distinct\b", cleaned_sql, re.IGNORECASE)),
        cte_count=count_ctes(cleaned_sql),
        has_subquery=detect_subquery(cleaned_sql),
        has_union=bool(re.search(r"\bunion(?:\s+all)?\b", cleaned_sql, re.IGNORECASE)),
        has_window_functions=detect_window_functions(cleaned_sql),
        window_functions=window_functions,
        aggregate_functions=aggregate_functions,
        selected_columns=selected_columns,
        table_aliases=table_aliases,
    )

    semantics.inferred_patterns = infer_patterns(semantics)
    semantics.dominant_pattern = infer_dominant_pattern(semantics)
    return semantics


def analyze_sql_file(path: str | Path) -> SqlSemantics:
    file_path = Path(path)
    model_name = file_path.stem.lower()
    sql = file_path.read_text(encoding="utf-8")
    return analyze_sql(model_name=model_name, sql=sql)


def analyze_sql_folder(folder_path: str | Path) -> dict[str, SqlSemantics]:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    results: dict[str, SqlSemantics] = {}
    for sql_file in sorted(folder.glob("*.sql")):
        semantics = analyze_sql_file(sql_file)
        results[semantics.model_name] = semantics

    return results
