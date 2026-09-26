# Individual Submission & Ownership Report

- **Submission Type:** `Individual Submission`
- **Ten nhom:** `MotMinhTui`
- **Ma nhom / Lop:** `K4-L3B-DAY10`
- **Tên Repository nộp bài:** `https://github.com/ntthduong/K4-L3B-MotMinhTui-Day10-Data-Pipeline-Data-Observability`

---

## Thanh Vien

| STT | Ho va ten | MSSV | Email | Vai tro & Phan cong cong viec | Bao cao ca nhan |
|---:|---|---|---|---|---|
| 1 | Nguyen Thi Thuy Duong | 2A202602905 | 26ai.duongntt@vinuni.edu.vn | Full Pipeline Owner | `report/individual_report.md` |

---

## Ownership

### Nguyen Thi Thuy Duong - 2A202602905

- **Vai tro:** Full Pipeline Owner.
- **Pham vi phu trach:** Raw ingestion, data cleaning, data observability, freshness monitoring, retrieval/indexing, evaluation, corruption/repair flow, reporting, and orchestration.
- **Cong viec da hoan thanh:**
  - CP0: Hoan thien ingestion Crossref trong `src/ingestion/crossref.py`, gom parser, fetcher, retry va local fallback.
  - CP1: Hoan thien cleaning trong `src/ingestion/cleaning.py`, sinh cleaned dataframe 24 dong voi `age_days` va `text_for_embedding`.
  - CP1: Hoan thien data quality/freshness trong `src/observability/quality.py` bang Great Expectations 1.x va Freshness SLA.
- **Artifacts da xac minh:**
  - `data/raw/crossref_response.json`
  - `data/raw/crossref_records.json`
  - `data/clean/papers_clean.csv`
  - `data/clean/papers_clean.json`
  - `data/quality/test_quality_report.json`
- **Ket qua xac minh hien tai:**
  - CP0: Tai/doc duoc 24 bai bao.
  - CP1: Clean thanh cong 24 dong.
  - CP1: Quality check status = True.
