from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run the baseline data pipeline end-to-end."""
    settings = load_settings()
    run_date = now_utc()

    records = fetch_source_records(settings)
    df = build_clean_dataframe(records, run_date)
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(df, settings.paths.eval_testset)
    else:
        test_set = build_test_set(df, settings.paths.eval_testset)

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records": len(records),
        "clean_rows": len(df),
        "test_questions": len(test_set),
        "indexed_documents": len(index.documents),
        "collection_name": index.collection_name,
        "embedding_model": settings.embedding_model,
        "run_date": run_date.isoformat(),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    print("Phase 1 baseline pipeline completed.")
    print(f"Raw records: {len(records)}")
    print(f"Clean rows: {len(df)}")
    print(f"Test questions: {len(test_set)}")
    print(f"Indexed documents: {len(index.documents)}")
    print(f"Retrieval hit rate: {evaluation.summary['retrieval_hit_rate']:.4f}")
    print(f"Mean token F1: {evaluation.summary['mean_token_f1']:.4f}")
    print(f"Report: {settings.paths.baseline_report}")
