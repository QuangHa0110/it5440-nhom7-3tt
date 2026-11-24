# ADR 0013 — Quét secret tích hợp, giá trị bị che từ lúc phát hiện

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [ADR 0005](0005-dung-lai-ma-nguon-mo.md), [ADR 0008](0008-llm-gateway-openai-compat-va-bi-mat.md)

## Bối cảnh

Với mã do bên thứ ba gửi về, secret bị commit nhầm là lỗi phổ biến và dễ phát hiện. Proposal để quét secret ngoài phạm vi các RQ nhưng cho phép bật để báo riêng.

## Quyết định

- **D1.** Thêm `SecretScanner` hiện thực `ScannerPort`, quét văn bản bằng mẫu regex (khóa đám mây, token, khóa riêng, JWT, gán `password=...`).
- **D2.** Mẫu nhận diện dùng chung với bộ che secret trước khi gửi LLM, đặt ở `core/secrets.py`.
- **D3.** **Giá trị secret bị che ngay khi phát hiện.** Cảnh báo, đoạn mã lưu trong kho, comment và chú thích đều chỉ chứa phiên bản đã che. Dấu vân tay tính trên bản đã che.
- **D4.** Cảnh báo secret đi qua cùng luồng với cảnh báo khác (cách A, B, C), nên LLM có thể phân biệt giá trị thật với giá trị giữ chỗ.
- **D5.** Có thể tắt bằng cấu hình `secrets.enabled: false`. Không dùng cho RQ1 đến RQ4 trừ khi tách riêng.

## Phương án khác

- **gitleaks hoặc trufflehog:** mạnh hơn nhưng thêm một tệp nhị phân phải cài. Có thể thay thế sau nhờ cổng `ScannerPort`.

## Hệ quả

- **Tốt hơn:** không thêm phụ thuộc, phát hiện được các loại secret phổ biến.
- **Tệ hơn:** độ phủ và độ chính xác thấp hơn công cụ chuyên dụng.
- **Từ nay phải đúng:** không có đường nào để giá trị secret nguyên bản rời khỏi bộ quét.
