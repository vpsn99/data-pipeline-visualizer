from __future__ import annotations

import re
from pathlib import Path

REF_PATTERN = re.compile(r"""ref\s*\(\s*['"]([a-zA-Z0-9_\.]+)['"]\s*\)""", re.IGNORECASE)

# Simple FROM / JOIN matcher:
# - captures identifiers like schema.table, db.schema.table, table_name
# - avoids subqueries like FROM (
FROM_JOIN_PATTERN = re.compile(
    r"""\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_\.\"]*)""",
    re.IGNORECASE,
)

CTE_PATTERN = re.compile(
    r"""\bwith\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(|,\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(""",
    re.IGNORECASE,
)


def extract_cte_names(sql: str) -> set[str]:
    """
    Extract CTE names from a WITH clause.
    Heuristic-based.
    """
    matches = CTE_PATTERN.findall(sql)
    ctes: set[str] = set()

    for first, second in matches:
        name = first or second
        if name:
            ctes.add(name.lower())

    return ctes


def remove_sql_comments(sql: str) -> str:
    """
    Remove SQL single-line and multi-line comments.
    This is heuristic-based and good enough for V1.
    """
    # Remove /* ... */ comments
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

    # Remove -- ... comments
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)

    return sql


def normalize_identifier(identifier: str) -> str:
    """
    Normalize a SQL identifier for dependency tracking.
    Examples:
      '"raw"."orders"' -> raw.orders
      'RAW.ORDERS' -> raw.orders
      'orders' -> orders
    """
    identifier = identifier.strip()

    # Remove quotes around parts
    identifier = identifier.replace('"', "")

    # Remove trailing punctuation that may appear in SQL
    identifier = identifier.rstrip(",;")

    return identifier.lower()


def extract_refs(sql: str) -> set[str]:
    """
    Extract dbt-style ref('model_name') dependencies.
    """
    matches = REF_PATTERN.findall(sql)
    return {normalize_identifier(m) for m in matches}


def extract_from_join_tables(sql: str) -> set[str]:
    """
    Extract table references from FROM and JOIN clauses.
    Heuristic-based for V1.
    """
    matches = FROM_JOIN_PATTERN.findall(sql)

    dependencies: set[str] = set()
    for match in matches:
        normalized = normalize_identifier(match)

        # Ignore likely subqueries or invalid captures
        if normalized in {"select", "("}:
            continue
        if normalized.startswith("("):
            continue

        dependencies.add(normalized)

    return dependencies


def extract_dependencies(sql: str) -> list[str]:
    """
    Extract all table/model dependencies from SQL text.

    Order:
    - dbt ref() dependencies
    - raw FROM/JOIN dependencies

    Deduplicated and sorted for stable output.
    """
    cleaned_sql = remove_sql_comments(sql)

    refs = extract_refs(cleaned_sql)
    from_join_tables = extract_from_join_tables(cleaned_sql)
    cte_names = extract_cte_names(cleaned_sql)

    dependencies = refs.union(from_join_tables)
    dependencies = {dep for dep in dependencies if dep not in cte_names}

    return sorted(dependencies)


def get_model_name_from_file(path: Path) -> str:
    """
    Use file stem as model name.
    Example:
      models/fct_sales.sql -> fct_sales
    """
    return path.stem.lower()


def parse_sql_file(path: Path) -> list[str]:
    """
    Read a SQL file and return extracted dependencies.
    """
    sql = path.read_text(encoding="utf-8")
    return extract_dependencies(sql)


def parse_sql_folder(folder_path: str | Path) -> dict[str, list[str]]:
    """
    Parse all .sql files in a folder and return a mapping:
      {model_name: [dependency1, dependency2, ...]}

    Self-dependencies are removed.
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    result: dict[str, list[str]] = {}

    for sql_file in sorted(folder.glob("*.sql")):
        model_name = get_model_name_from_file(sql_file)
        dependencies = parse_sql_file(sql_file)

        # remove self-dependency if present
        dependencies = [dep for dep in dependencies if dep != model_name]

        result[model_name] = dependencies

    return result
