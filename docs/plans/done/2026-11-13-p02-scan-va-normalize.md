# P02. Quét, đọc SARIF, chuẩn hóa và lấy cảnh báo mới

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Đóng:** cách A chạy được
- **Quyết định cho phép:** ADR 0005, 0011
- **Nhánh:** `trinq/scan/semgrep-and-normalize`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Cách A là mốc so sánh và là đầu vào của mọi cách khác.

## Ngoài phạm vi

SpotBugs (chỉ làm khi P05 xong và còn thời gian). CodeQL.

## Hiện trạng đã kiểm chứng

2026-11-13: các gói `semgrep`, `tree-sitter`, `tree-sitter-java` giải được phụ thuộc bằng `uv`. Chưa cài. `WebGoat` và `OWASP BenchmarkJava` truy cập được bằng `git ls-remote`.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `SarifReader` đọc SARIF 2.1.0 ra `Finding` thô, giữ vết luồng dữ liệu (`codeFlows`) nếu có | Test trên một SARIF mẫu đã commit trong `tests/fixtures/`, đủ trường | P01 |
| T2 | `SemgrepAdapter` chạy `semgrep` như tiến trình con có trần thời gian, trả SARIF | Test tích hợp (marker `integration`) trên một repo Java nhỏ cho ra ít nhất một cảnh báo | T1 |
| T3 | Ca thử phạm vi phân tích vết của Semgrep CE: một sink trong hàm khác file | Kết quả (có hay không báo xuyên file) ghi vào `docs/devlog/` | T2 |
| T4 | `Fingerprinter` gắn dấu vân tay, tìm hàm bao quanh bằng tree-sitter | Qua test ADR 0011 D5 trên mã Java thật | T1 |
| T5 | `Deduplicator` (ADR 0011 D3) | Test: hai cảnh báo chồng vùng thành một với hai nguồn | T4 |
| T6 | `BaselineDiff`: nhận hai tập, trả cảnh báo mới | Test trên cặp commit thật trong một repo Git tạo tạm | T5 |
| T7 | Dữ liệu thử: cặp commit có thêm một lỗ hổng SQL injection vào repo mẫu | `pr-triage run` giả lập cho ra đúng một cảnh báo mới | T6 |

## Cổng

```bash
make check && uv run pytest -m integration tests/scan
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Semgrep tải luật từ mạng, chậm hoặc không có mạng tại Z | Lần chạy đầu treo | Dùng bộ luật đã tải về `configs/semgrep/` và quét với `--config` cục bộ, ghi băm bộ luật |
| Dấu vân tay đổi khi định dạng lại | Test T4 fail | Chuẩn hóa khoảng trắng và chú thích trước khi băm |

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `make check` qua với 38 test (có integration chạy Semgrep thật). `SarifReader`, `SemgrepAdapter`, `SymbolIndex` (tree-sitter-java), `to_findings`, `deduplicate`, `new_findings`.
- **Khác kế hoạch:** `SymbolIndex` làm ở `context/` (không phải `normalize/`) để giữ ranh giới import, pipeline truyền hàm phân giải vào `normalize`. T7 (cặp commit thật) làm ở P05 cùng `gitrepo`. T3 cho kết quả âm có giá trị: CE không nối taint xuyên hàm.
- **Ghi ở:** devlog 2026-11-13 Semgrep CE.
