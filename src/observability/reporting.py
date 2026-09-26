from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a concise markdown report for the baseline pipeline."""
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in source_summary.items():
        lines.append(f"| `{key}` | {_format_value(value)} |")

    lines.extend(
        [
            "",
            "## Baseline Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| `samples` | {_format_value(metrics.get('samples'))} |",
            f"| `retrieval_hit_rate` | {_format_float(metrics.get('retrieval_hit_rate'))} |",
            f"| `mean_token_f1` | {_format_float(metrics.get('mean_token_f1'))} |",
            f"| `judge_accuracy` | {_format_float(metrics.get('judge_accuracy'))} |",
            f"| `mean_judge_score` | {_format_float(metrics.get('mean_judge_score'))} |",
            "",
            "## Data Quality",
            "",
            f"- Overall status: `{quality.get('success')}`",
            "",
            "| Check | Pass |",
            "| --- | --- |",
        ]
    )
    for check_name, passed in quality.get("checks", {}).items():
        lines.append(f"| `{check_name}` | `{passed}` |")

    lines.extend(
        [
            "",
            "## Freshness",
            "",
            "| Field | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in freshness.items():
        lines.append(f"| `{key}` | {_format_value(value)} |")

    ragas = metrics.get("ragas", {})
    lines.extend(
        [
            "",
            "## Ragas",
            "",
            f"`{_format_value(ragas)}`",
            "",
        ]
    )
    write_text(Path(report_path), "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
) -> None:
    """Write a markdown report comparing baseline, corrupted and repaired states."""
    metric_names = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]
    lines = [
        "# Corruption And Repair Comparison Report",
        "",
        "## Metrics Comparison",
        "",
        "| Metric | Baseline | Corrupted | Repaired | Corruption Delta | Repair Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for metric_name in metric_names:
        baseline = baseline_metrics.get(metric_name)
        corrupted = corrupted_metrics.get(metric_name)
        repaired = repaired_metrics.get(metric_name)
        lines.append(
            f"| `{metric_name}` | {_format_float(baseline)} | {_format_float(corrupted)} | {_format_float(repaired)} | "
            f"{_format_delta(corrupted, baseline)} | {_format_delta(repaired, corrupted)} |"
        )

    lines.extend(
        [
            "",
            "## Quality And Freshness",
            "",
            "| Signal | Baseline | Corrupted | Repaired |",
            "| --- | --- | --- | --- |",
            f"| Quality status | `{_optional_get(baseline_quality, 'success')}` | `{corrupted_quality.get('success')}` | `{repaired_quality.get('success')}` |",
            f"| Freshness status | `{_optional_get(baseline_freshness, 'is_fresh')}` | `{corrupted_freshness.get('is_fresh')}` | `{repaired_freshness.get('is_fresh')}` |",
            f"| Stale rows | `{_optional_get(baseline_freshness, 'stale_rows')}` | `{corrupted_freshness.get('stale_rows')}` | `{repaired_freshness.get('stale_rows')}` |",
            f"| Stale ratio | `{_format_float(_optional_get(baseline_freshness, 'stale_ratio'))}` | `{_format_float(corrupted_freshness.get('stale_ratio'))}` | `{_format_float(repaired_freshness.get('stale_ratio'))}` |",
            "",
            "## Corrupted Quality Checks",
            "",
            "| Check | Pass |",
            "| --- | --- |",
        ]
    )
    for check_name, passed in corrupted_quality.get("checks", {}).items():
        lines.append(f"| `{check_name}` | `{passed}` |")

    lines.extend(
        [
            "",
            "## Repaired Quality Checks",
            "",
            "| Check | Pass |",
            "| --- | --- |",
        ]
    )
    for check_name, passed in repaired_quality.get("checks", {}).items():
        lines.append(f"| `{check_name}` | `{passed}` |")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "The corrupted dataset intentionally violates row count, uniqueness, text length and freshness expectations. ",
            "The repaired dataset is rebuilt from trusted raw records, then re-cleaned, re-indexed and re-evaluated with the same test set.",
            "",
        ]
    )
    write_text(Path(report_path), "\n".join(lines))


def _format_float(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{float(value):.4f}"
    return _format_value(value)


def _format_value(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value).replace("\n", " ")


def _format_delta(value: Any, reference: Any) -> str:
    if isinstance(value, int | float) and isinstance(reference, int | float):
        return f"{float(value) - float(reference):+.4f}"
    return "N/A"


def _optional_get(payload: dict[str, Any] | None, key: str) -> Any:
    return payload.get(key) if payload else None
