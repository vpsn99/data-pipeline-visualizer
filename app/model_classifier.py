from __future__ import annotations

from collections import Counter


def classify_model_layer(model_name: str) -> str:
    """
    Infer the architectural layer of a model from its name.
    """
    name = model_name.lower()

    if name.startswith("src_"):
        return "source"

    if name.startswith("stg_"):
        return "staging"

    if name.startswith("int_"):
        return "intermediate"

    if name.startswith("dim_"):
        return "dimension"

    if name.startswith("fct_"):
        return "fact"

    if name.startswith("agg_"):
        return "aggregate"

    return "other"


def summarize_layers(semantic_map: dict) -> dict[str, int]:
    """
    Count models by architectural layer.
    """
    counter = Counter()

    for semantics in semantic_map.values():
        counter[semantics.model_layer] += 1

    return dict(counter)
