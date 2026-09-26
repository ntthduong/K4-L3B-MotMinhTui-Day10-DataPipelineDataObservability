from __future__ import annotations

from datetime import datetime
import re

import pandas as pd

from core.config import load_settings
from core.utils import compact_join, normalize_whitespace, write_csv
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw paper records into a dataframe ready for embedding."""
    rows: list[dict] = []
    run_ts = pd.Timestamp(run_date)
    if run_ts.tzinfo is not None:
        run_ts = run_ts.tz_convert(None)

    for record in records:
        paper_id = normalize_whitespace(record.paper_id).lower()
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        authors = [_clean_text(author) for author in record.authors if _clean_text(author)]
        categories = [_clean_text(category) for category in record.categories if _clean_text(category)]
        published = pd.to_datetime(record.published, errors="coerce")
        updated = pd.to_datetime(record.updated, errors="coerce")

        if not paper_id or not title or not summary or pd.isna(published):
            continue

        authors_joined = compact_join(authors or ["Unknown Author"])
        categories_joined = compact_join(categories or ["Uncategorized"])
        age_days = max(0, int((run_ts.normalize() - published.normalize()).days))
        published_text = published.date().isoformat()
        updated_text = updated.date().isoformat() if not pd.isna(updated) else published_text

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors or ["Unknown Author"],
                "categories": categories or ["Uncategorized"],
                "primary_category": categories[0] if categories else "Uncategorized",
                "published": published_text,
                "updated": updated_text,
                "age_days": age_days,
                "abs_url": normalize_whitespace(record.abs_url),
                "pdf_url": normalize_whitespace(record.pdf_url),
                "comment": _clean_text(record.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "text_for_embedding": _build_embedding_text(
                    title=title,
                    summary=summary,
                    authors_joined=authors_joined,
                    categories_joined=categories_joined,
                    published=published_text,
                ),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[df["summary_chars"] >= 40]
    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)

    settings = load_settings()
    write_csv(df, settings.paths.clean_csv)
    settings.paths.clean_json.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=True)
    return df


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return normalize_whitespace(text)


def _build_embedding_text(
    *,
    title: str,
    summary: str,
    authors_joined: str,
    categories_joined: str,
    published: str,
) -> str:
    return normalize_whitespace(
        f"Title: {title}\n"
        f"Authors: {authors_joined}\n"
        f"Published: {published}\n"
        f"Categories: {categories_joined}\n"
        f"Summary: {summary}"
    )
