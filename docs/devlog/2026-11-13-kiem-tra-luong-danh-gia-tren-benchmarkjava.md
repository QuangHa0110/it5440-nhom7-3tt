# Kiểm tra luồng đánh giá trên OWASP BenchmarkJava

- **Mức độ:** 🟢 ghi chú. **Đây là kiểm tra mã chạy, không phải kết quả của đề tài.**
- **Ngày:** 2026-11-13
- **Liên quan:** kế hoạch P07 T7, ADR 0003

## Phát hiện

Chạy `pr-triage run --base none` trên 120 file nhóm SQL injection của BenchmarkJava (30 cảnh báo từ luật taint viết tay), mô hình <mô-hình-thử-nghiệm>, rồi dùng nhãn của Benchmark (mức file) làm nhãn cuối bằng một script ngoài repo, tính số đo bằng `pr-triage eval metrics --split dev`:

| Cách | Loại được cảnh báo sai | Loại nhầm lỗi thật | Không xác định | Đúng |
|---|---|---|---|---|
| A (chỉ công cụ) | 0/7 | 0/23 | 0/30 | 23/30 = 76,7% |
| B (±10 dòng) | 2/7 = 28,6% | 2/23 = 8,7% | 6/30 = 20,0% | 19/30 = 63,3% |
| C (luồng dữ liệu) | 4/7 = 57,1% | 0/23 = 0,0% | 0/30 = 0,0% | 27/30 = 90,0% |

Tỉ lệ cảnh báo sai nền: 7/30 = 23,3% (Wilson 11,8% đến 40,9%). McNemar B so với C: chỉ B đúng 0, chỉ C đúng 8, p = 0,008. Tổng 54 441 token vào, 14 715 token ra, 115 giây cho 60 lần gọi (6 luồng song song).

Cùng bộ dữ liệu, cách B với cửa sổ ±25 dòng (lần thử trước) không cho `unknown` nào và khớp 24/30. Cửa sổ ±10 dòng cho 6 `unknown`: kích thước cửa sổ của cách B ảnh hưởng mạnh đến kết quả.

## Vì sao quan trọng

- Luồng đánh giá chạy thông từ cảnh báo đến bảng số đo, gồm Wilson, McNemar, lượt đọc tiết kiệm và khóa manifest.
- **Không dùng để kết luận C hơn B.** Mẫu nhỏ, nhãn Benchmark ở mức file, mô hình có thể đã thấy Benchmark khi huấn luyện, chưa tách `dev`/`eval`, và toàn bộ cảnh báo thuộc một lượt chạy nên khoảng bootstrap theo PR suy biến (một nhóm duy nhất).
- Bán kính cửa sổ của cách B phải được chốt trên tập `dev` trước khi khóa cấu hình, nếu không so sánh B với C có thể bị thiên lệch bởi một tham số chưa tinh chỉnh.

## Đề xuất điều chỉnh

- Thêm bán kính cửa sổ của cách B vào bước chỉnh trên `dev` và vào manifest. Hiện tham số này mặc định 10 và chưa nằm trong `configs/`.
- Báo cáo bootstrap theo PR chỉ có nghĩa khi có từ khoảng 10 PR trở lên.
