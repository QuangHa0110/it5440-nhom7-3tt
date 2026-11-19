# Kiểm thử ngày 2026-11-18

## Phạm vi

Kiểm tra webhook với payload tổng hợp, chạy kiểm chứng tự động trong môi trường không nạp `.env` của dự án, và xác minh app/tunnel sau khi khởi động lại. Bổ sung cùng ngày: kịch bản đánh giá A/B/C trên mã Java mã nguồn mở (tiêu chí K và R).

## Kịch bản

- [Xác thực chữ ký, allowlist, draft và retry trùng](scenarios/01-webhook-validation-and-retry.md)
- [Bộ test và xác minh app hoạt động](scenarios/02-suite-and-service-readiness.md)
- **[Kịch bản đánh giá A/B/C trên mã nguồn mở](scenarios/03-kich-ban-danh-gia-oss.md)**

## Kết quả và người thực hiện

- [Tổng hợp kết quả](results/verification-results.md)
- [Truy vết ca test-plan sang bằng chứng](results/traceability.md)
- **[Kết quả đánh giá A/B/C trên mã nguồn mở](results/03-ket-qua-danh-gia-oss.md)** (kèm đối chiếu tiêu chí K/R và cổng 5.7)
- [Người thực hiện và người yêu cầu](testers/tester-record.md)
