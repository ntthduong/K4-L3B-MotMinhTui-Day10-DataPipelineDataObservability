# Báo Cáo Individual Submission — Day 10: Data Pipeline & Data Observability

## 1. Thông Tin Bài Nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | MotMinhTui |
| Repository | https://github.com/ntthduong/K4-L3B-MotMinhTui-Day10-Data-Pipeline-Data-Observability |
| Hình thức | Individual Submission |
| Ngày hoàn thành | 2026-09-26 |

### Thành Viên Và Phân Công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Thị Thùy Dương | 2A202602905 | Full Pipeline Owner | Toàn bộ pipeline: ingestion, cleaning, observability, retrieval, evaluation, corruption, repair, reporting |

## 2. Tóm Tắt Kết Quả

Bài nộp đã hoàn thành các checkpoint chính từ CP0 đến CP5. Pipeline bắt đầu từ dữ liệu Crossref/local snapshot, parse thành `PaperRecord`, làm sạch thành dataframe 24 dòng, tạo `text_for_embedding`, build ChromaDB index bằng `sentence-transformers/all-MiniLM-L6-v2`, sinh bộ test 10 câu hỏi và đánh giá baseline. Baseline đạt `retrieval_hit_rate=1.0000`, `mean_token_f1=1.0000`, quality status `True` và freshness status `True`. Sau đó, pipeline tiêm 6 loại lỗi dữ liệu gồm drop records mới nhất, blank summary, inject noise, truncate title, stale date và duplicate rows. Dữ liệu corrupted làm `retrieval_hit_rate` giảm còn `0.5000`, `mean_token_f1` còn `0.7788`, quality và freshness đều fail. Cuối cùng, repair flow phục hồi dữ liệu từ `data/raw/crossref_records.json`, rebuild clean dataset, rebuilt repaired index và đánh giá lại trên cùng test set. Repaired metrics quay lại baseline với `retrieval_hit_rate=1.0000`, `mean_token_f1=1.0000`, quality `True` và freshness `True`.

## 3. Kiến Trúc Và Luồng Dữ Liệu

```text
Crossref API / local snapshot
    -> raw response/raw records
    -> parse PaperRecord
    -> cleaning và data modeling
    -> text_for_embedding
    -> ChromaDB vector index
    -> evaluation baseline
    -> quality/freshness reports
    -> synthetic corruption
    -> corrupted index và evaluation
    -> repair từ raw records
    -> repaired index và evaluation
    -> comparison report
```

### Trách Nhiệm Của Từng Khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API/local snapshot | Fetch, retry, parse DOI/title/abstract/authors/date | `data/raw/` | Nguyễn Thị Thùy Dương |
| Cleaning | Raw `PaperRecord` list | Normalize text, tính `age_days`, tạo `text_for_embedding` | `data/clean/` | Nguyễn Thị Thùy Dương |
| Embedding/index | Clean dataframe | Build ChromaDB collection bằng MiniLM | `data/chroma/`, `data/embeddings/` | Nguyễn Thị Thùy Dương |
| Evaluation | Test set + vector index | Tính hit rate, token F1, judge metrics | `data/results/` | Nguyễn Thị Thùy Dương |
| Observability | Clean/corrupted/repaired dataframe | Great Expectations 1.x và Freshness SLA | `data/quality/` | Nguyễn Thị Thùy Dương |
| Corruption/repair | Clean data và raw records | Tiêm 6 lỗi, repair từ raw source | corrupted/repaired artifacts | Nguyễn Thị Thùy Dương |
| Orchestration | Tất cả module | Chạy `phase1.py` và `corruption_flow.py` | `data/reports/` | Nguyễn Thị Thùy Dương |

## 4. Cách Tái Hiện Kết Quả

### Cấu Hình Không Chứa Secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini`, cấu hình qua `.env` |
| `LLM_MODEL` | `gemini-2.5-flash`, cấu hình qua `.env` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày |
| Ragas | Không chạy mặc định, cần `RUN_RAGAS=1` |

Không đưa API key, token hoặc nội dung `.env` vào báo cáo.

### Lệnh Cài Đặt

```bash
python -m pip install -e .
```

### Lệnh Chạy

Baseline pipeline:

```bash
python script/run_phase1.py
```

Corruption và repair flow:

```bash
python script/run_corruption_flow.py
```

### Kết Quả Tái Hiện

| Lệnh | Trạng thái | Bằng chứng |
| --- | --- | --- |
| `python script/run_phase1.py` | Thành công | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| `python script/run_corruption_flow.py` | Thành công | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, Cleaning Và Data Contract

### Nguồn Dữ Liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API với local snapshot fallback |
| Query | `agentic retrieval augmented generation large language model` |
| Filter | `from-pub-date:<computed>,has-abstract:true` |
| Số record nhận được | 24 |
| Retry/backoff | Retry cho `429/5xx`, fallback về `data/raw/` khi API lỗi |

### Raw Và Clean Schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | string | Có | DOI/document ID | Drop row nếu thiếu |
| `title` | string | Có | Tiêu đề paper | Normalize whitespace, drop row nếu thiếu |
| `summary` | string | Có | Abstract/summary | Bỏ JATS/XML tags, validate length |
| `authors` | list[string] | Có | Danh sách tác giả | Fallback `Unknown Author` |
| `categories` | list[string] | Có | Crossref subjects | Fallback `Uncategorized` |
| `published` | date string | Có | Ngày xuất bản | Parse từ `date-parts`, drop row nếu invalid |
| `age_days` | integer | Có | Tín hiệu freshness | Tính từ run date và `published` |
| `text_for_embedding` | string | Có | Nội dung đưa vào embedding | Ghép title, authors, date, categories, summary |

### Quy Tắc Cleaning

| Quy tắc | Quality dimension | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Drop record thiếu ID/title/summary/date | Completeness/Validity | 0 | Clean dataset vẫn có 24 dòng |
| Bỏ XML/JATS tags và normalize whitespace | Validity | 24 | `summary` không còn tag XML |
| Drop duplicate theo `paper_id` | Uniqueness | 0 | `paper_id_unique=True` |
| Tính `age_days` và tạo `text_for_embedding` | Freshness/Usability | 24 | Clean dataframe có đủ helper columns |

`text_for_embedding` được tạo từ 5 phần: title, authors, published date, categories và summary. Document ID dùng DOI trong `paper_id`. `age_days` là số ngày giữa run date và ngày xuất bản, dùng cho Freshness SLA.

## 6. Evaluation Setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | DOI trong `paper_id`, lưu ở `ground_truth_doc_ids` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 |
| Test set dùng chung | `data/eval/test_set.json` |

Test set được giữ nguyên cho baseline, corrupted và repaired để đảm bảo so sánh công bằng. Khi câu hỏi không đổi, thay đổi metric phản ánh tác động của dữ liệu/index thay vì thay đổi đề đánh giá.

## 7. Kết Quả Baseline

### Artifact Checklist

| Artifact | Đường dẫn | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | 24 records |
| Cleaned dataset | `data/clean/` | Có | 24 rows |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json`, `data/chroma/` | Có | Collection `papers-baseline` |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu hỏi |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit rate và F1 đều 1.0 |
| Quality/freshness | `data/quality/` | Có | Quality và freshness đều pass |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo Phase 1 |

### Baseline Metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | Top retrieved docs luôn chứa ground-truth document ID |
| `mean_token_f1` | 1.0000 | Câu trả lời rule-based khớp ground truth trong test set |
| `judge_accuracy` | 1.0000 | Judge đánh giá tất cả câu trả lời là đúng |
| `mean_judge_score` | 5.0000 | Điểm trung bình tối đa |
| Ragas | Skipped | Chưa set `RUN_RAGAS=1` |

## 8. Data Quality Và Freshness

### Quality Checks Baseline

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| Row count | Completeness | 24 dòng | Pass | `baseline_quality_report.json` |
| `paper_id` not null | Completeness | Không null | Pass | `baseline_quality_report.json` |
| `paper_id` unique | Uniqueness | Không trùng | Pass | `baseline_quality_report.json` |
| `title` length | Validity | 8 đến 300 ký tự | Pass | `baseline_quality_report.json` |
| `summary` length | Validity | 40 đến 5000 ký tự | Pass | `baseline_quality_report.json` |
| Freshness SLA | Timeliness | Stale ratio <= 0.25 | Pass | `freshness_report.json` |

### Freshness Baseline

| Thuộc tính | Giá trị |
| --- | --- |
| Latest published | 2026-07-22 |
| Oldest published | 2026-03-28 |
| Stale rows | 1 |
| Total rows | 24 |
| Stale ratio | 0.0417 |
| Threshold | 180 ngày |
| Trạng thái | Fresh/Pass |

## 9. Corruption Scenarios Và Repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| Drop latest records | Xóa 5 records mới nhất | 5 | Row count fail, mất tài liệu ground truth | Hit rate giảm | Rebuild từ raw records |
| Blank summary | Xóa rỗng summary | 3 | Summary length fail | Token F1 giảm ở một số câu | Re-clean từ raw records |
| Inject noise | Chèn noise vào summary | 4 | Nội dung embedding nhiễu | Retrieval/answer kém ổn định hơn | Rebuild text từ raw records |
| Truncate title | Cắt title thành `Bad` | 3 | Title length fail | Metadata kém chất lượng | Re-clean title từ raw records |
| Stale date | Đưa `published` về `2020-01-01` | 8 | Freshness fail | Stale ratio tăng 0.3636 | Recompute dates từ raw records |
| Duplicate rows | Nhân bản rows giữ nguyên `paper_id` | 3 | Uniqueness fail | Index chứa duplicate identity | Deduplicate qua cleaning từ raw records |

Corruption log có tại `data/results/corruption_log.json` và ghi đủ 6 loại lỗi, số row bị tác động và danh sách `paper_id` liên quan.

Repair không chỉnh trực tiếp corrupted data. Flow phục hồi đọc lại `data/raw/crossref_records.json`, chạy lại cleaning, rebuild ChromaDB collection `papers-repaired`, rồi evaluate lại trên cùng `data/eval/test_set.json`. Cách này đảm bảo repair dựa trên nguồn raw đáng tin cậy thay vì chỉ che lỗi ở output.

## 10. So Sánh Baseline, Corrupted Và Repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | -0.5000 | +0.5000 | Corruption làm mất/biến dạng tài liệu liên quan, repair phục hồi hoàn toàn |
| `mean_token_f1` | 1.0000 | 0.7788 | 1.0000 | -0.2212 | +0.2212 | Summary rỗng/nhiễu làm câu trả lời kém khớp hơn |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | -0.2000 | +0.2000 | Judge phát hiện suy giảm chất lượng câu trả lời |
| `mean_judge_score` | 5.0000 | 4.4000 | 5.0000 | -0.6000 | +0.6000 | Điểm trung bình giảm khi data bị lỗi |
| Quality checks | 1.0000 | 0.0000 | 1.0000 | -1.0000 | +1.0000 | Corrupted fail, repaired pass |
| Freshness status | 1.0000 | 0.0000 | 1.0000 | -1.0000 | +1.0000 | Stale ratio vượt ngưỡng ở corrupted, trở lại pass sau repair |

Kết luận nhân quả:

1. Drop latest records, blank summary, truncate title và duplicate rows làm quality gate fail; đồng thời `retrieval_hit_rate` giảm từ 1.0000 xuống 0.5000.
2. Stale date làm freshness status chuyển từ `True` sang `False` vì stale ratio tăng từ 0.0417 lên 0.3636.
3. Repair từ raw records làm quality/freshness quay lại `True`, đồng thời `retrieval_hit_rate` và `mean_token_f1` quay lại 1.0000.

## 11. Vấn Đề Tích Hợp Quan Trọng

- **Triệu chứng:** Khi chạy lệnh verify có tiếng Việt trên Windows PowerShell, Python báo `UnicodeEncodeError`.
- **Nguyên nhân:** stdout mặc định dùng encoding `cp1252`, không encode được một số ký tự tiếng Việt.
- **Cách xử lý:** Set `$env:PYTHONIOENCODING='utf-8'` trước khi chạy các lệnh verify.
- **Cách xác minh:** Các lệnh CP0-CP5 in được tiếng Việt và hoàn tất thành công.

## 12. Giới Hạn Và Hướng Cải Thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Ragas chưa chạy mặc định | Chưa có thêm các metric faithfulness/context precision từ Ragas | Set `RUN_RAGAS=1` và ghi kết quả vào report |
| Bộ test có 10 câu | Phạm vi đánh giá còn nhỏ | Tăng số câu hỏi và đa dạng hóa question type |
| Corruption deterministic | Tốt cho tái hiện nhưng chưa bao phủ toàn bộ lỗi production | Thêm random seed và nhiều mức độ corruption |
| Chưa có dashboard bonus | Observability hiện ở dạng JSON/Markdown | Có thể thêm Streamlit/Gradio dashboard |

## 13. Checklist Trước Khi Nộp

- [x] Thông tin bài nộp và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Báo cáo vai trò cá nhân đã hoàn thành.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
