# P01. Mô hình miền, cổng và kho lưu trữ

- **Status:** queued
- **Người làm:** trinq (với Claude Code)
- **Đóng:** nền cho P02 đến P07
- **Quyết định cho phép:** ADR 0004, 0006, 0011
- **Nhánh:** `trinq/core/domain-and-store`
- **Bắt đầu / Kết thúc:** — / —

---

## Bối cảnh

Mọi gói khác phụ thuộc `core` và `store`. Phải có trước.

## Ngoài phạm vi

Không viết bộ hiện thực nào của `ScannerPort`, `LlmPort`, `ScmPort`. Không PostgreSQL.

## Hiện trạng đã kiểm chứng

2026-11-13: `make check` qua với 2 test; `src/pr_triage/{core,store,pipeline}` đã tạo, rỗng.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | Dataclass bất biến cho `Finding`, `Occurrence`, `ContextBundle`, `Verdict`, `PrRun`, `DisplayedAlert`, `FeedbackEvent`, `Label`, `Adjudication` (theo sơ đồ 7) | `mypy` strict qua, test dựng và so sánh bằng nhau cho từng lớp | — |
| T2 | Năm `Protocol` trong `core/ports.py` | `mypy` qua, có bộ giả (`FakeScanner`...) trong `tests/fakes.py` hiện thực đủ phương thức | T1 |
| T3 | Thuật toán dấu vân tay (ADR 0011) | Test: không đổi khi chỉ thêm dòng phía trên hoặc đổi định dạng, đổi khi đổi mã khớp; có trường phiên bản | T1 |
| T4 | `SqlStore`: migration SQL đánh số, WAL, các phương thức của `StorePort` | Test round-trip mọi thực thể trên SQLite trong bộ nhớ và trên tệp | T1, T2 |
| T5 | `BlobStore`: ghi theo băm nội dung, đọc lại, không ghi trùng | Test: ghi hai lần cùng nội dung ra một tệp | T4 |
| T6 | Bí danh hóa tên file, người, repo | Test: `Exporter` giả không xuất được giá trị gốc | T4 |
| T7 | Test ranh giới import (ADR 0004 D4) bằng `ast` | Test fail khi thêm `from pr_triage.bot import` vào `core` thử nghiệm, qua khi bỏ | T1 |

## Cổng

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Cổng sai ngay từ đầu, phải sửa khi làm P02 đến P06 | Sửa `core/ports.py` ở hơn hai plan sau | Sửa cổng trong một commit riêng, ghi vào devlog |

---

## Kết quả

*Điền khi đóng.*
