from __future__ import annotations

from pathlib import Path
from typing import Any


def format_list(values: list[str]) -> list[str]:
    """
    Format a list as Markdown bullet lines.
    """
    if not values:
        return ["None"]

    return [f"- {value}" for value in values]


def safe_filename(model_name: str) -> str:
    """
    Convert model names into safe markdown filenames.
    """
    return model_name.replace("/", "_").replace("\\", "_") + ".md"


def generate_model_doc(model_name: str, metadata: dict[str, Any]) -> str:
    """
    Generate Markdown documentation for one model.
    """
    lines: list[str] = []

    lines.append(f"# {model_name}")
    lines.append("")

    lines.append("## Overview")
    lines.append("")
    lines.append(f"- **Node Type:** {metadata.get('node_type', 'unknown')}")
    lines.append(f"- **Layer:** {metadata.get('layer', 'other')}")
    lines.append(f"- **Complexity:** {metadata.get('complexity_level', 'unknown')}")
    lines.append(f"- **Complexity Score:** {metadata.get('complexity_score', 0)}")
    lines.append(f"- **Dominant Pattern:** {metadata.get('dominant_pattern') or 'None'}")
    lines.append("")

    lines.append("## Lineage")
    lines.append("")

    lines.append("### Dependencies")
    lines.append("")
    lines.extend(format_list(metadata.get("dependencies", [])))
    lines.append("")

    lines.append("### Downstream Models")
    lines.append("")
    lines.extend(format_list(metadata.get("downstream_models", [])))
    lines.append("")

    lines.append("## SQL Intelligence")
    lines.append("")
    lines.append(f"- **Join Count:** {metadata.get('join_count', 0)}")
    lines.append(f"- **Join Types:** {', '.join(metadata.get('join_types', [])) or 'None'}")
    lines.append("")

    lines.append("### Join Keys")
    lines.append("")
    lines.extend(format_list(metadata.get("join_keys", [])))
    lines.append("")

    lines.append("### Aggregate Functions")
    lines.append("")
    lines.extend(format_list(metadata.get("aggregate_functions", [])))
    lines.append("")

    lines.append("### Group By Columns")
    lines.append("")
    lines.extend(format_list(metadata.get("group_by_columns", [])))
    lines.append("")

    lines.append("### Filters")
    lines.append("")
    lines.append(f"- **Where Clause:** {metadata.get('where_clause') or 'None'}")
    lines.append("")

    selected_columns = metadata.get("selected_columns", [])
    if selected_columns:
        lines.append("## Selected Columns")
        lines.append("")
        lines.extend(format_list(selected_columns))
        lines.append("")

    lines.append("## Parser Diagnostics")
    lines.append("")
    lines.append(f"- **Parser Used:** {metadata.get('parser_used') or 'N/A'}")
    lines.append(f"- **Parse Status:** {metadata.get('parse_status') or 'N/A'}")

    parse_error = metadata.get("parse_error")
    if parse_error:
        lines.append(f"- **Parse Error:** {parse_error}")
    else:
        lines.append("- **Parse Error:** None")

    lines.append("")

    return "\n".join(lines)


def generate_catalog_docs(
    catalog: dict[str, dict[str, Any]],
    output_dir: str | Path = "output/catalog",
) -> list[Path]:
    """
    Generate one Markdown file per model in the catalog.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []

    for model_name, metadata in sorted(catalog.items()):
        output_file = directory / safe_filename(model_name)
        output_file.write_text(
            generate_model_doc(model_name, metadata),
            encoding="utf-8",
        )
        written_files.append(output_file)

    return written_files
