# ADR 0008 — Truy cập LLM qua API kiểu OpenAI, cấu hình bằng biến môi trường, khóa không bao giờ vào repo

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [architecture.md](../architecture.md) mục 8.2; proposal 6.6, 10, 15

## Bối cảnh

Nhóm dùng một dịch vụ LLM kiểu OpenAI trong lúc phát triển. Địa chỉ, danh sách mô hình và khóa của dịch vụ này là thông tin nội bộ, không ghi trong repo.

Dịch vụ LLM dùng khi phát triển là dịch vụ **bên ngoài** so với công ty Z. Với dữ liệu của Z, nó thuộc loại "LLM cloud" của proposal và chỉ được dùng khi Z đồng ý bằng văn bản. Với mã nguồn mở và dữ liệu công khai (phát triển, RQ4) thì dùng tự do.

## Quyết định

- **D1.** Một `OpenAICompatClient` duy nhất, gọi `POST {base_url}/chat/completions` bằng `httpx`, dùng được cho cổng này, Ollama và vLLM tại chỗ.
- **D2.** Cấu hình qua biến môi trường `PR_TRIAGE_LLM_BASE_URL`, `PR_TRIAGE_LLM_API_KEY`, `PR_TRIAGE_LLM_MODEL`. Mẫu ở `.env.example`, giá trị thật ở `.env` (đã trong `.gitignore`).
- **D3.** **Khóa API không được xuất hiện trong repo, log, prompt đã lưu hay manifest.** Client che khóa khi ghi log. Test kiểm tra chuỗi khóa không có trong kho blob.
- **D4.** Mã mô hình đầy đủ (kèm tiền tố `openai/`) được ghi vào `Verdict.model_id` và manifest.
- **D5.** `Redactor` chạy trước mọi lần gửi. Có cờ cấu hình `allow_external` mặc định `false` cho dữ liệu lấy từ Z. Khi `false`, client từ chối gọi tới địa chỉ không nằm trong danh sách cho phép.
- **D6.** `temperature` bằng 0 và `seed` cố định. Kiểm tra `finish_reason` và từ chối nhận định bị cắt cụt.

## Phương án khác

- **SDK `openai`:** chấp nhận được, nhưng `httpx` đủ cho một endpoint và giảm phụ thuộc.
- **LiteLLM:** hợp khi gọi nhiều nhà cung cấp. Ở đây chỉ một giao thức.

## Hệ quả

- **Tốt hơn:** đổi mô hình hay chuyển sang máy chủ tại chỗ chỉ cần đổi biến môi trường.
- **Tệ hơn:** không thấy được độ trễ và giới hạn tốc độ của cổng trước khi chạy thật.
- **Từ nay phải đúng:** không dùng dịch vụ LLM bên ngoài cho mã của Z cho đến khi Z đồng ý bằng văn bản.
