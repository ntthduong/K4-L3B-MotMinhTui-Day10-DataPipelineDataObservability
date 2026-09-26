from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref work-list payload into normalized paper records."""
    records: list[PaperRecord] = []
    seen_ids: set[str] = set()

    for item in payload.get("message", {}).get("items", []):
        paper_id = normalize_whitespace(str(item.get("DOI", ""))).lower()
        title = _first_text(item.get("title"))
        summary = _clean_abstract(str(item.get("abstract", "")))
        if not paper_id or not title or not summary or paper_id in seen_ids:
            continue

        authors = _parse_authors(item.get("author", []))
        categories = [normalize_whitespace(str(value)) for value in item.get("subject", []) if str(value).strip()]
        published = _date_from_parts(item.get("published")) or _date_from_parts(item.get("published-print"))
        updated = _date_from_datetime(item.get("created", {}).get("date-time")) or published
        url = normalize_whitespace(str(item.get("URL") or f"https://doi.org/{paper_id}"))

        if not published:
            continue

        seen_ids.add(paper_id)
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref records, falling back to checked-in snapshots when needed."""
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    payload: dict[str, Any] | None = None
    try:
        payload = _request_crossref_payload(settings)
        write_json(settings.paths.raw_api_response, payload)
    except requests.RequestException:
        if settings.paths.raw_api_response.exists():
            payload = json.loads(settings.paths.raw_api_response.read_text(encoding="utf-8"))
        elif settings.paths.raw_records_json.exists():
            return load_raw_records(settings.paths.raw_records_json)
        else:
            raise

    records = parse_crossref_payload(payload)
    _write_records(settings.paths.raw_records_json, records)
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load normalized raw records from a JSON snapshot."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [PaperRecord(**item) for item in payload]


def _request_crossref_payload(settings: Settings) -> dict[str, Any]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    url = "https://api.crossref.org/works"
    retry_statuses = {429, 500, 502, 503, 504}
    last_error: requests.RequestException | None = None

    for attempt in range(4):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code in retry_statuses:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2**attempt)

    if last_error:
        raise last_error
    raise RuntimeError("Crossref request failed after retries.")


def _first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        return normalize_whitespace(str(value[0]))
    return normalize_whitespace(str(value or ""))


def _clean_abstract(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return normalize_whitespace(text)


def _parse_authors(value: Any) -> list[str]:
    authors: list[str] = []
    for author in value if isinstance(value, list) else []:
        given = normalize_whitespace(str(author.get("given", "")))
        family = normalize_whitespace(str(author.get("family", "")))
        name = normalize_whitespace(f"{given} {family}")
        if name:
            authors.append(name)
    return authors or ["Unknown Author"]


def _date_from_parts(value: Any) -> str:
    parts = value.get("date-parts", [[]])[0] if isinstance(value, dict) else []
    if not parts:
        return ""
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def _date_from_datetime(value: Any) -> str:
    if not value:
        return ""
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()


def _write_records(path: Path, records: list[PaperRecord]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps([asdict(record) for record in records], indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
