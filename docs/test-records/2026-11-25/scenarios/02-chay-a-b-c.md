# Kịch bản 02 — Chạy A, B, C trên các PR đã đăng ký

| Trường | Nội dung |
|---|---|
| Mục tiêu | Mỗi PR trong [bảng đăng ký](../results/dang-ky-pr.md) có một lượt `pr-triage run --variants B,C` để B và C xét cùng tập cảnh báo của A. |
| Tiền điều kiện | Bảng đăng ký đã commit (P6). LLM qua cổng tương thích OpenAI, khóa chỉ ở biến môi trường. |
| Tham số | Theo `configs/eval/run.yml` (tag `eval-freeze-1`): `--snippet-radius 40 --display C --no-secrets`, prompt `v1`, `--budget-pr-tokens 3000000` (trần vận hành). |
| Lệch so với `eval-freeze-1` | (1) Bộ luật: `p/default` theo hướng dẫn chọn repo và PR (mặc định của pipeline), không phải `java-injection.yml` như `run.yml`. (2) Mô hình: máy chạy chưa có khóa của cổng LLM nhóm, nên chạy bằng một mô hình DeepSeek khác qua cổng khác. Tên mô hình ghi trong nhật ký nộp kèm qua kênh riêng, và `manifest_hash` của các lượt chạy này khác với lượt dùng mô hình đã khóa. Nếu nhóm cần đúng mô hình đã khóa, chạy lại B, C trên cùng bảng đăng ký, phần A giữ nguyên. |
| Kết quả mong đợi | Mọi lượt có `triage-result.json` với `status: ok`, không lỗi LLM. Mỗi cảnh báo của A có đúng một nhãn B và một nhãn C. `summarize_runs.py` cho bảng số nhãn, thời gian và token mỗi PR. |
| Ngoài phạm vi | Gán nhãn đáp án (do người, gán chéo và mù theo mục 6 của hướng dẫn). Đăng comment lên PR của repo gốc. |

## Thực hiện và kết quả

Chạy 13:26–14:42 (+07), hai luồng song song, sau khi bảng đăng ký đã commit lúc 13:25:57. Chi tiết và số liệu:
[kết quả A, B, C](../results/ket-qua-abc.md).

| Mong đợi | Thực tế | Đạt |
|---|---|---|
| Mỗi PR đã đăng ký có `triage-result.json` | 13/13. Ba lượt hỏng ở lần đầu (SQLite bị khóa, quét quá trần 300 giây) được chạy lại và xong | Có |
| `status: ok`, không lỗi LLM | 6 `ok`, 7 `degraded`: 23 nhãn bị cắt cụt (`finish_reason=length`), 4 nhãn C bị HTTP 403 ở lớp chống bot trước cổng LLM | Không |
| Mỗi cảnh báo của A có đúng một nhãn B và một nhãn C | 56 nhãn B, 56 nhãn C cho 56 cảnh báo | Có |
| `summarize_runs.py` cho bảng theo PR | Có, nằm trong gói nộp riêng (không commit để giữ mù cho bước gán nhãn) | Có |

**Kết luận: Đạt một phần.** Đủ dữ liệu để gán nhãn và tính chỉ số, nhưng 27/112 nhãn (24%) không có phán đoán của mô
hình: 23 bị cắt cụt, 4 bị chặn ở đường truyền. Khi tính chỉ số, loại 4 nhãn 403 khỏi mẫu số của C. Nếu nhóm đổi
`max_tokens` hoặc dùng mô hình đã khóa thì chạy lại B, C trên cùng bảng đăng ký.
