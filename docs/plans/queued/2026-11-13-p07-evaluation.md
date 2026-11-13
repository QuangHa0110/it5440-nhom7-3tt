# P07. Luồng đánh giá ngoại tuyến

- **Status:** queued
- **Người làm:** trinq (với Claude Code) và hotamago
- **Đóng:** phiếu gán nhãn mù, số đo, khóa cấu hình, xuất ẩn danh
- **Quyết định cho phép:** ADR 0006, proposal 7
- **Nhánh:** `trinq/evaluation/offline-eval`
- **Bắt đầu / Kết thúc:** — / —

---

## Bối cảnh

Phần này biến dữ liệu của pipeline thành số đo của RQ1 đến RQ3. Có thể kiểm chứng sớm trên **OWASP BenchmarkJava**, bộ có nhãn đúng sai sẵn. Nhãn của Benchmark chỉ dùng để kiểm tra mã đo hoạt động đúng, không dùng làm nhãn của đề tài.

## Ngoài phạm vi

Gán nhãn thật (việc của người). Khảo sát lập trình viên. Không dùng AI để tạo nhãn đáp án (proposal 10).

## Hiện trạng đã kiểm chứng

Chưa viết gì. `scipy` và `statsmodels` giải được phụ thuộc.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `Metrics`: khoảng Wilson, McNemar, kappa, bootstrap theo PR, lượt đọc tiết kiệm trên mỗi lỗi thật bị mất | Test so với giá trị tính tay và với ví dụ của proposal mục 2 (171 và 5,4) | P01 |
| T2 | `PoolBuilder`: chia `dev`/`eval` theo thời gian merge, một repo chỉ cho `eval` | Test trên dữ liệu giả | P01 |
| T3 | `BlindLabeling` xuất phiếu CSV theo người, thứ tự xáo riêng | Test: phiếu không chứa trường nào của `Verdict`; mã nguồn xuất phiếu không import bảng nhận định | P01 |
| T4 | Nhập nhãn, tính kappa, hàng đợi phân xử | Test: kappa dưới 0,6 chặn bước phân xử | T3 |
| T5 | `FreezeGuard`: manifest băm cấu hình, từ chối chạy `eval` khi lệch | Test: sửa một prompt thì `metrics --split eval` từ chối | P03 |
| T6 | `Exporter`: bảng tổng hợp, gộp nhóm dưới ngưỡng k, bỏ tên file | Test: không có giá trị gốc nào của bảng bí danh trong đầu ra | P01 T6 |
| T7 | Kiểm chứng trên BenchmarkJava: chạy A, B, C, tính số đo với nhãn của Benchmark | Bảng số đo vào devlog, đánh dấu rõ là kiểm tra mã, không phải kết quả của đề tài | P05, T1 |

## Cổng

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Rò nhận định LLM sang phiếu gán nhãn | Test T3 fail | Chặn merge cho đến khi sửa |
| BenchmarkJava giống dữ liệu huấn luyện của mô hình | Kết quả cao bất thường | Ghi chú rõ trong devlog, không dùng để kết luận về mô hình |

---

## Kết quả

*Điền khi đóng.*
