# Semgrep CE không nối taint xuyên hàm, và không sinh vết luồng dữ liệu trong SARIF

- **Mức độ:** 🟢 ghi chú (củng cố động cơ của cách C, không đổi thiết kế)
- **Ngày:** 2026-11-13
- **Liên quan:** ADR 0005 D5, kế hoạch P02 T3, kiến trúc mục 8.1

## Phát hiện

Chạy Semgrep CE 1.185.0 với luật taint viết tay (`configs/semgrep/java-injection.yml`) trên mã mẫu có hai đường:

- `showDirect`: `request.getParameter` đi thẳng tới `executeQuery` trong cùng hàm. **Báo** (dòng 15).
- `show` gọi `dao.find(status)`, `find` nối chuỗi rồi `executeQuery` ở file khác. **Không báo** bằng luật taint. Chỉ luật khớp mẫu "nối chuỗi trong executeQuery" báo ở `OrderDao.java:10`.

SARIF đầu ra, kể cả khi thêm `--dataflow-traces`, **không có `codeFlows`** cho kết quả taint trong lần thử này. Luật cục bộ bị gắn tiền tố bằng đường dẫn tuyệt đối của file cấu hình vào `ruleId`.

Kiểm thử: `tests/scan/test_semgrep_adapter.py::test_semgrep_ce_does_not_report_cross_function_taint`.

## Vì sao quan trọng

- Đây là đúng khoảng trống mà ngữ cảnh luồng dữ liệu (cách C) nhắm vào: công cụ chỉ thấy nửa đường, LLM cần phần còn lại.
- Không thể dùng vết của công cụ làm hạt giống cho bộ trích (P04 T7). Bộ trích phải tự lần ngược từ sink.
- `.semgrepignore` mặc định của Semgrep loại thư mục `tests/`, nên mã test bị bỏ qua khi quét. Proposal muốn đánh dấu riêng mã test thay vì bỏ.

## Đề xuất điều chỉnh

- P04 T7 chuyển thành tùy chọn: dùng vết khi có, không phụ thuộc vào nó.
- Bộ chuyển đổi Semgrep bỏ tiền tố đường dẫn của id luật cục bộ (đã làm).
- Khi chạy tại Z, quyết định có truyền `.semgrepignore` riêng để quét cả mã test hay không, rồi gắn cờ `is_test_code` ở khâu gán nhãn.
