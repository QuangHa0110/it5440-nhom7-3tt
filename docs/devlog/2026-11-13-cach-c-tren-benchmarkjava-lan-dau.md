# Cách C trên OWASP BenchmarkJava: số đo lần đầu

- **Mức độ:** 🟢 ghi chú (kiểm tra mã chạy, không phải kết quả của đề tài)
- **Ngày:** 2026-11-13
- **Liên quan:** kế hoạch P04 T8, ADR 0003, sơ đồ 6

## Phát hiện

Trên 30 cảnh báo taint của Semgrep CE (luật viết tay) lấy từ 120 file nhóm SQL injection của OWASP BenchmarkJava:

| Số đo của bộ trích (cách C) | Giá trị |
|---|---|
| Tìm được sink theo danh mục | 30/30 |
| Tìm được nguồn dữ liệu | 26/30 |
| Cảnh báo có ghi `missing` | 4/30 (đều là "nguồn dữ liệu chưa xác định") |
| Thời gian trích | tổng 2,1 s cho 30 cảnh báo, lớn nhất 142 ms |
| Đoạn mã trung bình mỗi bundle | khoảng 1,8 nghìn ký tự, 2,8 đoạn |

Trước hai sửa đổi, số cảnh báo có `missing` là 30/30 và nguồn tìm được chỉ 18/30:

- Điểm vào của servlet (`doGet`, `doPost`) bị truy ngược nơi gọi, ra hàng trăm kết quả vô nghĩa. Nay danh mục có `entry_points` và `framework_types`.
- Sink không có đối số (`statement.executeQuery()`) cho bundle không có gì để lần. Nay bộ trích lần theo đối tượng nhận lời gọi.

Thử cách B và cách C với <mô-hình-thử-nghiệm> trên cùng 30 cảnh báo:

| | B (±25 dòng) | C (luồng dữ liệu) |
|---|---|---|
| likely_true / likely_false | 27 / 3 | 26 / 4 |
| Khớp nhãn Benchmark | 24 | 27 |
| Trái nhãn | 6 | 3 |
| Token vào | 28 947 | 31 166 |

## Vì sao quan trọng

- Mẫu rất nhỏ, nhãn Benchmark ở mức file, mô hình có thể đã thấy Benchmark khi huấn luyện, và chưa tách `dev`/`eval`. Con số này chỉ cho biết mã chạy đúng, không được dùng làm kết luận về C so với B.
- Độ phủ nguồn 26/30 và `missing` thấp (4/30) cho thấy bộ trích bằng cú pháp đủ dùng trên Benchmark. Benchmark có cấu trúc đơn giản (một file, nguồn và sink cùng hàm hoặc qua một hàm phụ), nên tỉ lệ này sẽ thấp hơn trên mã thật.
- Chi phí token của C chỉ hơn B khoảng 8%.

## Đề xuất điều chỉnh

- Chưa cần Joern. Đo lại `missing` trên repo thật trước khi quyết định (ADR 0003 D6).
- Bốn ca không tìm thấy nguồn (ví dụ `BenchmarkTest00108.java:92`) cần xem tay để biết là giới hạn của bộ trích hay kiểu nguồn chưa có trong danh mục.
