# Kịch bản 02 — Chạy A, B, C trên các PR đã đăng ký

| Trường | Nội dung |
|---|---|
| Mục tiêu | Mỗi PR trong [bảng đăng ký](../results/dang-ky-pr.md) có một lượt `pr-triage run --variants B,C` để B và C xét cùng tập cảnh báo của A. |
| Tiền điều kiện | Bảng đăng ký đã commit (P6). LLM qua cổng tương thích OpenAI, khóa chỉ ở biến môi trường. |
| Tham số | Theo `configs/eval/run.yml` (tag `eval-freeze-1`): `--snippet-radius 40 --display C --no-secrets`, prompt `v1`, `--budget-pr-tokens 3000000` (trần vận hành). |
| Lệch so với `eval-freeze-1` | (1) Bộ luật: `p/default` theo hướng dẫn chọn repo và PR (mặc định của pipeline), không phải `java-injection.yml` như `run.yml`. (2) Mô hình: không dùng được cổng LLM của nhóm, nên chạy bằng một mô hình DeepSeek khác qua cổng khác. Tên mô hình ghi trong nhật ký nộp kèm qua kênh riêng, và `manifest_hash` của các lượt chạy này khác với lượt dùng mô hình đã khóa. Nếu nhóm cần đúng mô hình đã khóa, chạy lại B, C trên cùng bảng đăng ký, phần A giữ nguyên. |
| Kết quả mong đợi | Mọi lượt có `triage-result.json` với `status: ok`, không lỗi LLM. Mỗi cảnh báo của A có đúng một nhãn B và một nhãn C. `summarize_runs.py` cho bảng số nhãn, thời gian và token mỗi PR. |
| Ngoài phạm vi | Gán nhãn đáp án (do người, gán chéo và mù theo mục 6 của hướng dẫn). Đăng comment lên PR của repo gốc. |

## Thực hiện và kết quả

*Ghi sau khi chạy, xem [kết quả A, B, C](../results/ket-qua-abc.md).*
