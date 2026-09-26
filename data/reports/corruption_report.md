# Báo Cáo So Sánh Corruption Và Repair

## 1. Mục Tiêu

Báo cáo này so sánh ba trạng thái của pipeline RAG:

| Trạng thái | Ý nghĩa |
| --- | --- |
| Baseline | Dữ liệu sạch, index sạch, quality/freshness pass |
| Corrupted | Dữ liệu bị tiêm lỗi có chủ đích để mô phỏng sự cố production |
| Repaired | Dữ liệu được phục hồi từ raw trusted source và đánh giá lại |

Mục tiêu là chứng minh corruption làm giảm chất lượng retrieval/answer, đồng thời repair flow có thể phục hồi quality, freshness và metrics về mức baseline.

## 2. So Sánh Metrics

| Metric | Baseline | Corrupted | Repaired | Thay đổi do corruption | Phục hồi sau repair |
| --- | ---: | ---: | ---: | ---: | ---: |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | -0.5000 | +0.5000 |
| `mean_token_f1` | 1.0000 | 0.7788 | 1.0000 | -0.2212 | +0.2212 |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | -0.2000 | +0.2000 |
| `mean_judge_score` | 5.0000 | 4.4000 | 5.0000 | -0.6000 | +0.6000 |

## 3. Quality Và Freshness

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality status | `True` | `False` | `True` |
| Freshness status | `True` | `False` | `True` |
| Stale rows | `1` | `8` | `1` |
| Stale ratio | `0.0417` | `0.3636` | `0.0417` |

## 4. Corrupted Quality Checks

| Check | Kết quả |
| --- | --- |
| `row_count` | `False` |
| `paper_id_not_null` | `True` |
| `paper_id_unique` | `False` |
| `title_not_null` | `True` |
| `summary_length_valid` | `False` |
| `freshness_sla` | `False` |

Corrupted dataset fail đúng kỳ vọng vì số dòng không còn 24, `paper_id` bị trùng, summary có dòng rỗng, title có dòng bị cắt ngắn, và stale ratio vượt ngưỡng 0.25.

## 5. Repaired Quality Checks

| Check | Kết quả |
| --- | --- |
| `row_count` | `True` |
| `paper_id_not_null` | `True` |
| `paper_id_unique` | `True` |
| `title_not_null` | `True` |
| `summary_length_valid` | `True` |
| `freshness_sla` | `True` |

Repaired dataset pass vì được rebuild từ `data/raw/crossref_records.json`, sau đó chạy lại cleaning, rebuild ChromaDB index và evaluate lại trên cùng test set.

## 6. Corruption Scenarios

| Scenario | Mô tả | Số record bị tác động |
| --- | --- | ---: |
| `drop_latest_records` | Xóa 5 records mới nhất | 5 |
| `blank_summary` | Làm rỗng summary | 3 |
| `inject_noise` | Chèn noise vào summary | 4 |
| `truncate_title` | Cắt title xuống dưới ngưỡng chất lượng | 3 |
| `stale_date` | Đưa ngày xuất bản về `2020-01-01` | 8 |
| `duplicate_rows` | Nhân bản rows giữ nguyên `paper_id` | 3 |

Log chi tiết nằm ở `data/results/corruption_log.json`.

## 7. Kết Luận

Corruption làm pipeline suy giảm rõ rệt: `retrieval_hit_rate` giảm từ 1.0000 xuống 0.5000, `mean_token_f1` giảm từ 1.0000 xuống 0.7788, quality status chuyển từ `True` sang `False`, và freshness status cũng chuyển sang `False`. Sau repair, dữ liệu được phục hồi từ raw trusted source, quality/freshness pass lại và toàn bộ metrics chính quay về mức baseline. Điều này chứng minh quality gate và repair flow phát hiện được silent data failure và phục hồi hiệu năng RAG một cách có kiểm chứng.
