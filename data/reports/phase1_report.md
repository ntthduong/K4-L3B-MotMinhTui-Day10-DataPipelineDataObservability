# Phase 1 Baseline Report

## Source Summary

| Field | Value |
| --- | --- |
| `source_api` | Crossref REST API |
| `source_query` | agentic retrieval augmented generation large language model |
| `source_filter` | from-pub-date:2026-03-30,has-abstract:true |
| `raw_records` | 24 |
| `clean_rows` | 24 |
| `test_questions` | 10 |
| `indexed_documents` | 24 |
| `collection_name` | papers-baseline |
| `embedding_model` | sentence-transformers/all-MiniLM-L6-v2 |
| `run_date` | 2026-09-26T04:01:48.074230+00:00 |

## Baseline Metrics

| Metric | Value |
| --- | ---: |
| `samples` | 10 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5.0000 |

## Data Quality

- Overall status: `True`

| Check | Pass |
| --- | --- |
| `row_count` | `True` |
| `paper_id_not_null` | `True` |
| `paper_id_unique` | `True` |
| `title_not_null` | `True` |
| `summary_length_valid` | `True` |
| `freshness_sla` | `True` |

## Freshness

| Field | Value |
| --- | --- |
| `latest_published` | 2026-07-22 |
| `oldest_published` | 2026-03-28 |
| `stale_rows` | 1 |
| `total_rows` | 24 |
| `stale_ratio` | 0.041666666666666664 |
| `threshold_days` | 180 |
| `max_stale_ratio` | 0.25 |
| `is_fresh` | True |

## Ragas

`{'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}`
