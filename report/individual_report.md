# Báo Cáo Vai Trò Cá Nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông Tin Cá Nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Thị Thùy Dương |
| MSSV | 2A202602905 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | MotMinhTui |
| Hình thức | Individual Submission |
| Vai trò chính | Full Pipeline Owner |
| Repository | https://github.com/ntthduong/K4-L3B-MotMinhTui-Day10-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai Trò Và Phạm Vi Công Việc

### Phần Việc Sở Hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw ingestion | `src/ingestion/crossref.py` | Crossref API/local snapshot | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành CP0 |
| Data cleaning | `src/ingestion/cleaning.py` | Raw `PaperRecord` list | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Hoàn thành CP1 |
| Data observability | `src/observability/quality.py` | Clean/corrupted/repaired dataframe | Quality và freshness reports | Hoàn thành CP1, CP4, CP5 |
| Test set | `src/evaluation/testset.py` | Clean dataframe | `data/eval/test_set.json` | Hoàn thành CP2 |
| Vector index | `src/retrieval/index.py` | Clean/corrupted/repaired dataframe | ChromaDB collections và embedding manifests | Hoàn thành CP2, CP4, CP5 |
| Baseline pipeline | `src/pipelines/phase1.py` | Raw records và config | Baseline metrics, answers, phase report | Hoàn thành CP3 |
| Corruption và repair | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Clean data và raw records | Corrupted/repaired metrics, comparison report | Hoàn thành CP4, CP5 |
| Reporting | `src/observability/reporting.py`, `report/*.md` | Metrics và quality artifacts | Markdown reports | Hoàn thành |

### Việc Hỗ Trợ Ngoài Phạm Vi Chính

| Hoạt động | Module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Debug encoding trên Windows PowerShell | CP0-CP5 verification commands | Dùng `$env:PYTHONIOENCODING='utf-8'` để in tiếng Việt không lỗi |
| Kiểm tra artifact sau từng checkpoint | `data/clean/`, `data/results/`, `data/quality/`, `data/reports/` | Đảm bảo số liệu trong báo cáo khớp file JSON/Markdown thực tế |

## 3. Kết Quả Theo Vai Trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Hoàn thiện parser và loader Crossref | `src/ingestion/crossref.py` | 24 normalized records | `fetch_source_records()` trả về 24 bài báo |
| Hoàn thiện cleaning dataframe | `src/ingestion/cleaning.py` | Clean dataframe 24 dòng | `data/clean/papers_clean.json` |
| Hoàn thiện GX quality gate và freshness | `src/observability/quality.py` | Quality status baseline `True` | `data/quality/baseline_quality_report.json` |
| Sinh test set benchmark | `src/evaluation/testset.py` | 10 câu hỏi, 4 question types | `data/eval/test_set.json` |
| Build baseline index | `LocalEmbeddingIndex.build()` | ChromaDB collection `papers-baseline`, 24 docs | `data/embeddings/papers_embeddings.json` |
| Chạy baseline pipeline | `src/pipelines/phase1.py` | Hit rate 1.0000, token F1 1.0000 | `data/results/baseline_metrics.json` |
| Tiêm corruption | `src/ingestion/corruption.py` | 6 loại lỗi, quality fail | `data/results/corruption_log.json` |
| Repair từ raw records | `src/pipelines/corruption_flow.py` | Repaired metrics quay lại baseline | `data/results/repaired_metrics.json` |

Output quan trọng nhất là bộ so sánh ba trạng thái trong `data/reports/corruption_report.md`: baseline đạt 1.0000, corrupted giảm xuống 0.5000 hit rate, repaired phục hồi lại 1.0000.

## 4. Giải Thích Kỹ Thuật Đã Thực Hiện

### Vấn Đề Cần Giải Quyết

Pipeline RAG phụ thuộc trực tiếp vào chất lượng dữ liệu. Nếu dữ liệu bị thiếu, trùng lặp, stale hoặc nhiễu, retrieval và câu trả lời có thể suy giảm mà hệ thống không nhất thiết crash. Vì vậy, cần xây dựng pipeline có lineage rõ ràng, quality gate tự động, benchmark evaluation và cơ chế repair từ nguồn raw đáng tin cậy.

### Cách Triển Khai

Ingestion ưu tiên đọc normalized snapshot local khi không yêu cầu refresh để đảm bảo tái hiện ổn định. Parser chuẩn hóa DOI, title, abstract, authors, categories và ngày xuất bản thành `PaperRecord`. Cleaning loại XML/JATS tags, normalize whitespace, parse date, tính `age_days`, tạo các cột helper và build `text_for_embedding`. Quality gate dùng Great Expectations 1.x cho row count, not-null, uniqueness và text length checks; freshness đo bằng tỷ lệ stale rows có `age_days > 180`.

Evaluation set gồm 10 câu hỏi thuộc 4 loại: `summary`, `authors`, `date`, `categories`. Cùng test set được dùng cho baseline, corrupted và repaired để so sánh công bằng. Corruption suite tiêm 6 lỗi có chủ đích. Repair flow không sửa trực tiếp corrupted dataset mà rebuild dữ liệu từ `data/raw/crossref_records.json`, sau đó re-clean, re-index và evaluate lại.

### Input, Output Và Contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/raw/crossref_response.json`, `data/raw/crossref_records.json`, clean dataframe, test set |
| Output | Clean/corrupted/repaired datasets, Chroma indexes, metrics JSON, quality JSON, reports |
| Module phụ thuộc | `core.config`, `core.utils`, `ingestion.crossref`, `retrieval.index` |
| Module sử dụng output | `evaluation.metrics`, `observability.quality`, `observability.reporting` |
| Điều kiện lỗi cần xử lý | API rate limit, missing fields, duplicate DOI, invalid date, stale records, noisy text |

### Cách Xác Minh

```bash
$env:PYTHONIOENCODING='utf-8'; python script/run_phase1.py
$env:PYTHONIOENCODING='utf-8'; python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Baseline chạy thành công; corrupted làm metrics giảm và quality fail; repaired phục hồi metrics và quality.
- **Kết quả thực tế:** CP0-CP5 đều hoàn thành, artifacts sinh đầy đủ.
- **Artifact/log:** `data/results/`, `data/quality/`, `data/reports/`, `data/clean/`, `data/embeddings/`.

## 5. Một Quyết Định Kỹ Thuật Quan Trọng

- **Bối cảnh:** Pipeline cần chạy được kể cả khi Crossref API bị rate limit hoặc mất mạng.
- **Các phương án đã cân nhắc:** Luôn gọi API mỗi lần chạy; hoặc ưu tiên local snapshot và chỉ refresh khi cấu hình yêu cầu.
- **Phương án đã chọn:** Ưu tiên local snapshot, hỗ trợ API refresh có retry/backoff và fallback.
- **Lý do:** Tăng reproducibility, giảm phụ thuộc mạng, vẫn giữ khả năng refresh dữ liệu khi cần.
- **Bằng chứng:** CP0 đọc được 24 bài báo từ artifact local và các pipeline sau tái hiện được cùng kết quả.

## 6. Một Lỗi Hoặc Blocker Đã Xử Lý

- **Triệu chứng/lỗi nguyên văn:** `UnicodeEncodeError: 'charmap' codec can't encode character` khi in tiếng Việt trong PowerShell.
- **Lệnh hoặc bước tái hiện:** Chạy lệnh verify có chuỗi tiếng Việt trên Windows terminal mặc định.
- **Nguyên nhân gốc:** Python stdout dùng encoding `cp1252`, không encode được một số ký tự tiếng Việt.
- **Cách xử lý:** Đặt `$env:PYTHONIOENCODING='utf-8'` trước khi chạy lệnh verify.
- **Cách xác minh sau khi sửa:** Các lệnh CP0-CP5 in đúng kết quả tiếng Việt.
- **Điều học được:** Cần cấu hình encoding ổn định khi chạy script có Unicode trên Windows.

## 7. Hiểu Biết Về Luồng End-To-End

1. Dữ liệu đi từ Crossref/local snapshot vào parser, chuyển thành `PaperRecord`, sau đó cleaning tạo dataframe có `text_for_embedding`. Dataframe này được đưa vào ChromaDB để build vector index.
2. Evaluation set chứa câu hỏi, ground truth và `ground_truth_doc_ids`. Retrieval hit rate kiểm tra liệu các document ID đúng có xuất hiện trong top retrieved docs hay không; answer quality dùng token F1 và judge score.
3. Quality checks kiểm tra schema/content contract như row count, not-null, uniqueness và length. Freshness monitoring tập trung vào tuổi dữ liệu qua `age_days` và stale ratio.
4. Cùng test set được dùng cho baseline, corrupted và repaired để đảm bảo khác biệt metric đến từ dữ liệu/index, không đến từ câu hỏi khác nhau.
5. Repair thành công khi dữ liệu được phục hồi từ raw trusted source, quality/freshness pass lại và repaired metrics quay lại gần hoặc bằng baseline.

## 8. Phân Tích Kết Quả

### Metrics Chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | Corruption làm mất/biến dạng tài liệu liên quan, repair phục hồi hoàn toàn |
| `mean_token_f1` | 1.0000 | 0.7788 | 1.0000 | Summary rỗng/nhiễu làm câu trả lời kém khớp hơn |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 | Judge phát hiện suy giảm ở corrupted state |
| `mean_judge_score` | 5.0000 | 4.4000 | 5.0000 | Điểm trung bình giảm khi data bị lỗi |
| Quality checks | True | False | True | Quality gate phát hiện corruption và pass lại sau repair |
| Freshness status | True | False | True | Stale ratio vượt ngưỡng ở corrupted và phục hồi sau repair |

### Kết Luận Từ Số Liệu

1. Drop records mới nhất, blank summary, truncate title và duplicate rows làm quality gate fail; đồng thời `retrieval_hit_rate` giảm từ 1.0000 xuống 0.5000.
2. Stale date làm stale ratio tăng từ 0.0417 lên 0.3636, khiến freshness status chuyển từ `True` sang `False`.
3. Repair từ raw records làm quality/freshness quay lại `True`, `retrieval_hit_rate` và `mean_token_f1` quay lại 1.0000.

Corruption ảnh hưởng rõ nhất là drop latest records vì một số paper trong test set bị loại khỏi corrupted index, làm retrieval không thể tìm đúng document ID. Kết quả phù hợp với kỳ vọng: quality/freshness phát hiện lỗi trước khi metrics repaired phục hồi.

## 9. Điều Học Được Và Hướng Cải Thiện

### Ba Điều Quan Trọng Nhất

1. Raw snapshot và normalized records giúp pipeline có data lineage và reproducibility tốt hơn khi API bên ngoài không ổn định.
2. Data quality nên kết hợp contract checks với freshness SLA vì dữ liệu có thể đúng schema nhưng đã quá cũ.
3. Chất lượng RAG phụ thuộc trực tiếp vào dữ liệu đầu vào; missing/stale/noisy records có thể gây silent failure nếu không có observability gate.

### Nếu Có Thêm Thời Gian

Có thể bật `RUN_RAGAS=1` để bổ sung faithfulness/context metrics, mở rộng test set nhiều hơn 10 câu, và xây dashboard observability để trực quan hóa quality/freshness theo thời gian.

## 10. Cam Kết Của Thành Viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ một module riêng lẻ.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo khác.

**Họ và tên:** Nguyễn Thị Thùy Dương

**Ngày xác nhận:** 2026-09-26
