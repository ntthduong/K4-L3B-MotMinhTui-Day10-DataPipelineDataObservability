from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a deterministic 10-question benchmark from the cleaned corpus."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "published",
        "categories_joined",
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Clean dataframe is missing required columns: {sorted(missing_columns)}")
    if len(df) < 10:
        raise ValueError("At least 10 cleaned papers are required to build the benchmark test set.")

    records = df.head(10).to_dict(orient="records")
    question_types = [
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
    ]

    test_set: list[dict[str, Any]] = []
    for index, (record, question_type) in enumerate(zip(records, question_types, strict=True), start=1):
        test_set.append(_build_question(index, record, question_type))

    write_json(output_path, test_set)
    return test_set


def _build_question(index: int, record: dict[str, Any], question_type: str) -> dict[str, Any]:
    title = str(record["title"])
    paper_id = str(record["paper_id"])

    if question_type == "summary":
        question = f"What is the paper '{title}' about?"
        ground_truth = first_sentence(str(record["summary"]))
    elif question_type == "authors":
        question = f"Who authored the paper '{title}'?"
        ground_truth = str(record["authors_joined"])
    elif question_type == "date":
        question = f"When was the paper '{title}' published?"
        ground_truth = str(record["published"])
    elif question_type == "categories":
        question = f"What categories are assigned to the paper '{title}'?"
        ground_truth = str(record["categories_joined"])
    else:
        raise ValueError(f"Unsupported question type: {question_type}")

    return {
        "id": f"q{index:03d}",
        "question_type": question_type,
        "question": question,
        "ground_truth": ground_truth,
        "ground_truth_doc_ids": [paper_id],
    }
