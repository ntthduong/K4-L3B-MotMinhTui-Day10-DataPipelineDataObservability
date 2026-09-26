from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import normalize_whitespace, write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate deterministic data corruption scenarios for CP4."""
    corrupted = df.copy(deep=True).reset_index(drop=True)
    log: list[dict[str, Any]] = []

    latest_indices = corrupted.sort_values("published", ascending=False).head(5).index.tolist()
    dropped_ids = corrupted.loc[latest_indices, "paper_id"].tolist()
    corrupted = corrupted.drop(index=latest_indices).reset_index(drop=True)
    log.append(
        {
            "scenario": "drop_latest_records",
            "description": "Dropped the five latest records to simulate missing fresh documents.",
            "affected_rows": len(dropped_ids),
            "paper_ids": dropped_ids,
        }
    )

    blank_indices = corrupted.head(3).index.tolist()
    blank_ids = corrupted.loc[blank_indices, "paper_id"].tolist()
    corrupted.loc[blank_indices, "summary"] = ""
    log.append(
        {
            "scenario": "blank_summary",
            "description": "Blanked summaries for several records.",
            "affected_rows": len(blank_ids),
            "paper_ids": blank_ids,
        }
    )

    noise_indices = corrupted.iloc[3:7].index.tolist()
    noise_ids = corrupted.loc[noise_indices, "paper_id"].tolist()
    noise = " ZXQ_NOISE @@ ## unrelated tokens hallucination drift "
    corrupted.loc[noise_indices, "summary"] = corrupted.loc[noise_indices, "summary"].astype(str) + noise * 3
    log.append(
        {
            "scenario": "inject_noise",
            "description": "Injected repeated noisy tokens into summaries.",
            "affected_rows": len(noise_ids),
            "paper_ids": noise_ids,
        }
    )

    truncate_indices = corrupted.iloc[7:10].index.tolist()
    truncate_ids = corrupted.loc[truncate_indices, "paper_id"].tolist()
    corrupted.loc[truncate_indices, "title"] = "Bad"
    log.append(
        {
            "scenario": "truncate_title",
            "description": "Truncated titles below the quality threshold.",
            "affected_rows": len(truncate_ids),
            "paper_ids": truncate_ids,
        }
    )

    stale_indices = corrupted.tail(8).index.tolist()
    stale_ids = corrupted.loc[stale_indices, "paper_id"].tolist()
    corrupted.loc[stale_indices, "published"] = "2020-01-01"
    corrupted.loc[stale_indices, "updated"] = "2020-01-01"
    corrupted.loc[stale_indices, "age_days"] = 2400
    log.append(
        {
            "scenario": "stale_date",
            "description": "Moved records far into the past to violate freshness SLA.",
            "affected_rows": len(stale_ids),
            "paper_ids": stale_ids,
        }
    )

    duplicate_rows = corrupted.iloc[0:3].copy(deep=True)
    duplicate_ids = duplicate_rows["paper_id"].tolist()
    corrupted = pd.concat([corrupted, duplicate_rows], ignore_index=True)
    log.append(
        {
            "scenario": "duplicate_rows",
            "description": "Duplicated records while keeping the same paper_id.",
            "affected_rows": len(duplicate_ids),
            "paper_ids": duplicate_ids,
        }
    )

    corrupted["summary"] = corrupted["summary"].fillna("").astype(str).map(normalize_whitespace)
    corrupted["title"] = corrupted["title"].fillna("").astype(str).map(normalize_whitespace)
    corrupted["summary_chars"] = corrupted["summary"].str.len()
    corrupted["text_for_embedding"] = corrupted.apply(_build_text_for_embedding, axis=1)
    corrupted = corrupted.reset_index(drop=True)

    write_json(
        output_log_path,
        {
            "input_rows": len(df),
            "output_rows": len(corrupted),
            "scenarios": log,
        },
    )
    return corrupted


def _build_text_for_embedding(row: pd.Series) -> str:
    return normalize_whitespace(
        f"Title: {row.get('title', '')}\n"
        f"Authors: {row.get('authors_joined', '')}\n"
        f"Published: {row.get('published', '')}\n"
        f"Categories: {row.get('categories_joined', '')}\n"
        f"Summary: {row.get('summary', '')}"
    )
