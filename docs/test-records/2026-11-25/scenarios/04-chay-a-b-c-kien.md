# Kịch bản 04 — Chạy A, B, C trên các PR đã đăng ký (kien)

| Trường | Nội dung |
|---|---|
| Mục tiêu | Mỗi PR trong [bảng đăng ký](../results/dang-ky-pr-kien.md) có một lượt `pr-triage run --variants B,C` để B và C xét cùng tập cảnh báo của A |
| Tiền điều kiện | Danh sách PR đã xác định chỉ theo A. LLM qua endpoint tương thích OpenAI |
| Tham số | `--snippet-radius 40 --display C --no-secrets`, prompt `v1`, bộ luật `p/default`, mô hình `claude-sonnet-5-5` |
| Kết quả mong đợi | Mọi lượt có `triage-result.json` với `status: ok`, không lỗi LLM. Mỗi cảnh báo của A có đúng một nhãn B và một nhãn C. `summarize_runs.py` cho bảng theo PR |
| Ngoài phạm vi | Gán nhãn đáp án. Đăng comment lên PR của repo gốc |

## Thực hiện và kết quả

Chạy tuần tự 38 PR. Chi tiết: [kết quả A, B, C](../results/ket-qua-abc-kien.md).

| Mong đợi | Thực tế | Đạt |
|---|---|---|
| Mỗi PR đã đăng ký có `triage-result.json` | 38/38 | Có |
| `status: ok`, không lỗi LLM | 38 `ok`, 0 lỗi | Có |
| Mỗi cảnh báo của A có đúng một nhãn B và một nhãn C | 173 nhãn B, 173 nhãn C cho 173 cảnh báo | Có |
| `summarize_runs.py` cho bảng theo PR | Có, nằm trong gói nộp riêng | Có |

**Kết luận: Đạt.**
