# P04. Ngữ cảnh luồng dữ liệu (cách C)

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Đóng:** cách C chạy được, có số đo `missing`
- **Quyết định cho phép:** ADR 0003, 0005
- **Nhánh:** `trinq/context/dataflow-extractor`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Đây là phần phân tích chương trình chính của đề tài và là phần nhóm có thể khác với `sift-sast` (ADR 0005). Thuật toán ở sơ đồ 6.

## Ngoài phạm vi

Phân tích luồng dữ liệu đầy đủ như CodeQL hay Joern. Ngôn ngữ ngoài Java trong đợt này.

## Hiện trạng đã kiểm chứng

2026-11-13: `tree-sitter-java` giải được phụ thuộc. Chưa viết gì.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `SymbolIndex` bằng tree-sitter-java: hàm, lớp, vị trí, lời gọi theo tên | Test trên một dự án Java nhỏ: tìm được nơi gọi và thân hàm | P02 T4 |
| T2 | Danh mục nguồn, sink, hàm làm sạch cho SQLi, XSS, command injection, path traversal, ở `configs/context/java.yml` | File tải được và qua kiểm tra schema; mỗi CWE có ít nhất ba mục | — |
| T3 | Cắt lùi trong một hàm: từ đối số của sink về phép gán và lời gọi sinh ra nó | Test trên ba mẫu: gán trực tiếp, nối chuỗi, qua biến trung gian | T1, T2 |
| T4 | Mở rộng xuyên hàm tối đa 2 bước (tham số, kết quả lời gọi), ghi mơ hồ vào `missing` | Test: hai hàm trùng tên cho ra `missing` kèm k ứng viên | T3 |
| T5 | Trần dung lượng và thời gian, cắt theo thứ tự ưu tiên | Test: vượt trần thì giữ sink và hàm làm sạch, ghi phần bị cắt | T4 |
| T6 | `DataflowProvider` hiện thực `ContextPort`, đóng gói `ContextBundle` có băm | Test: cùng đầu vào cho cùng băm | T5 |
| T7 | Dùng vết luồng dữ liệu của Semgrep làm hạt giống nếu có | Test: có vết thì bundle chứa đúng nguồn của vết | T6, P02 T3 |
| T8 | Đo trên OWASP BenchmarkJava (có nhãn sẵn): tỉ lệ bundle có `missing`, thời gian trích | Bảng số đo vào devlog; quyết định có cần Joern hay không | T6 |

## Cổng

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Tỉ lệ `missing` cao (trên 50%) | Số đo T8 | Mở ADR mới xem xét Joern hoặc quay lại ADR 0003 |
| Hàm trùng tên nhiều | Nhiều `missing` mơ hồ | Phân giải theo kiểu của đối tượng gọi khi tree-sitter cho phép, còn lại ghi `missing` |

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `DataflowProvider` (cách C) với `Catalog` nạp từ `configs/context/java.yml`, lần ngược từ sink về nguồn, tối đa 2 bước gọi, ghi `missing`, trần dung lượng và thời gian. Trên 30 cảnh báo Benchmark: nguồn tìm thấy 26/30, `missing` ở 4/30, trích 2,1 s tổng.
- **Khác kế hoạch:** T7 (dùng vết của Semgrep làm hạt giống) bỏ vì Semgrep CE không sinh vết (devlog Semgrep CE). Thêm `entry_points` và `framework_types` vào danh mục, lần theo đối tượng nhận lời gọi khi sink không có đối số.
- **Ghi ở:** devlog 2026-11-13 (cách C trên Benchmark).
