# Kịch bản 02 — Bộ test và readiness của dịch vụ

| Trường | Nội dung |
|---|---|
| Mục tiêu | Kiểm tra chất lượng tự động của repo và khả năng nhận webhook sau khi khởi động app/tunnel. |
| Kết quả mong đợi | Lint, typecheck và pytest hoàn tất; app trả health/readiness tốt; ping có chữ ký qua public tunnel được chấp nhận. |

## Thực hiện và kết quả

1. Chạy Ruff check, Ruff format check và MyPy: đều đạt.
2. Chạy pytest từ thư mục làm việc cô lập để không tự nạp `.env` ở repo: **237 passed, 1 skipped**. Test bị skip là live LLM test vì tiến trình pytest không có biến cấu hình LLM.
3. `make check` chạy trực tiếp trong repo trước đó có một test lỗi môi trường: CLI nạp `.env` thật sau khi test chủ động xóa alias salt, khiến test gọi GitHub bằng token giả và nhận HTTP 401. Chạy lại toàn bộ pytest ở thư mục cô lập thì đạt; không sửa mã nguồn trong lần kiểm tra này.
4. Khởi động lại FastAPI và Cloudflare Quick Tunnel; endpoint health local và public trả `{"status":"ok"}`, readiness trả `{"status":"ready"}`. Ping có HMAC hợp lệ gửi qua tunnel trả HTTP `200`/`pong`.
5. Yêu cầu GitHub redeliver một ping delivery đã có; server nhận webhook và trả HTTP `200`.

**Kết luận:** Đạt cho lint/typecheck/pytest trong điều kiện cô lập và kiểm tra dịch vụ. Live LLM unit test không chạy trong pytest; phần triage LLM đã được xác minh riêng qua các PR end-to-end ngày 2026-11-17.
