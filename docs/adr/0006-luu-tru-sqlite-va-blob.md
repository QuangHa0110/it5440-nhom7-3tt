# ADR 0006 — Lưu trữ bằng SQLite (WAL) và kho blob trên hệ tệp, đặt trong vùng của Z

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [architecture.md](../architecture.md) mục 6, 9; proposal 10

## Bối cảnh

Dữ liệu gồm lượt chạy, cảnh báo, ngữ cảnh, nhận định, nhãn và phản hồi, cỡ vài trăm đến vài nghìn dòng, kèm các đoạn văn bản lớn (SARIF, prompt, phản hồi thô). Mã nguồn và prompt chứa mã phải ở lại trong Z.

## Quyết định

- **D1.** Bảng quan hệ lưu trong SQLite, chế độ WAL, truy cập qua `sqlite3` của thư viện chuẩn, không dùng ORM.
- **D2.** Văn bản lớn lưu thành blob trên hệ tệp, đặt tên theo băm SHA-256 của nội dung, bảng chỉ giữ tham chiếu.
- **D3.** Lược đồ nằm trong các file migration SQL đánh số, áp dụng tuần tự khi mở kho.
- **D4.** Bảng `Label` và `Adjudication` tách khỏi `Verdict`. Mã xuất phiếu gán nhãn không được truy vấn `Verdict`.
- **D5.** Kho nằm trong vùng của Z nên lưu giá trị gốc (cần cho gán nhãn và đọc mã). Bí danh hóa (HMAC với muối nằm trong Z) được áp ở hai chỗ: người thao tác ngay khi thu `FeedbackEvent`, và mọi tên file, người, repo khi `Exporter` xuất. Sửa ngày 2026-11-13 khi làm P01, trước khi ADR được chấp nhận.
- **D6.** `FeedbackEvent` chỉ thêm, không sửa.

## Phương án khác

- **PostgreSQL:** chịu được nhiều ghi đồng thời nhưng thêm một dịch vụ phải xin Z cài. Dùng khi Z chạy nhiều agent song song, nhờ cổng `StorePort` việc đổi là cục bộ.
- **Tệp JSON/Parquet:** khó truy vấn quan hệ và khó đảm bảo tính nhất quán.

## Hệ quả

- **Tốt hơn:** không cần dịch vụ ngoài, một file DB và một thư mục để sao lưu, tái lập được.
- **Tệ hơn:** ghi đồng thời bị giới hạn. Các job CI của một PR chạy tuần tự nên chấp nhận được.
- **Từ nay phải đúng:** kho nằm trên máy mà Z kiểm soát, quyền truy cập theo danh sách Z duyệt.
