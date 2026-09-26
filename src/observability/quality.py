from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
)
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run Great Expectations checks plus the lab freshness gate."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
    data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
    batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_batch_{report_name}")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        ExpectTableRowCountToBeBetween(min_value=settings.max_results, max_value=settings.max_results),
        ExpectColumnValuesToNotBeNull(column="paper_id"),
        ExpectColumnValuesToBeUnique(column="paper_id"),
        ExpectColumnValuesToNotBeNull(column="title"),
        ExpectColumnValueLengthsToBeBetween(column="title", min_value=8, max_value=300),
        ExpectColumnValueLengthsToBeBetween(column="summary", min_value=40, max_value=5000),
    ]
    gx_results = [batch.validate(expectation).to_json_dict() for expectation in expectations]
    freshness = _freshness_payload(df, settings)

    checks = {
        "row_count": len(df) == settings.max_results,
        "paper_id_not_null": bool(df["paper_id"].notna().all()) if "paper_id" in df else False,
        "paper_id_unique": bool(df["paper_id"].is_unique) if "paper_id" in df else False,
        "title_not_null": bool(df["title"].notna().all()) if "title" in df else False,
        "summary_length_valid": bool(df["summary"].str.len().between(40, 5000).all()) if "summary" in df else False,
        "freshness_sla": freshness["is_fresh"],
    }
    payload = {
        "report_name": report_name,
        "success": all(result.get("success", False) for result in gx_results) and all(checks.values()),
        "checks": checks,
        "freshness": freshness,
        "gx_results": gx_results,
    }

    report_path = _quality_report_path(settings, report_name)
    write_json(report_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize dataset freshness against the configured SLA."""
    payload = _freshness_payload(df, settings)
    write_json(Path(report_path), payload)
    return payload


def _freshness_payload(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    total_rows = len(df)
    if total_rows == 0:
        return {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "threshold_days": settings.freshness_threshold_days,
            "max_stale_ratio": 0.25,
            "is_fresh": False,
        }

    published = pd.to_datetime(df["published"], errors="coerce") if "published" in df else pd.Series(dtype="datetime64[ns]")
    age_days = pd.to_numeric(df["age_days"], errors="coerce") if "age_days" in df else pd.Series(dtype="float64")
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows
    return {
        "latest_published": published.max().date().isoformat() if not published.empty and not pd.isna(published.max()) else None,
        "oldest_published": published.min().date().isoformat() if not published.empty and not pd.isna(published.min()) else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": stale_ratio <= 0.25,
    }


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    if report_name == "baseline":
        return settings.paths.baseline_quality_report
    if report_name == "corrupted":
        return settings.paths.corrupted_quality_report
    return settings.paths.quality_dir / f"{report_name}_quality_report.json"
