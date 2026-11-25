# 2026-11-25 — Lọc PR bằng A và chạy A, B, C trên repo Java mã nguồn mở

Phần việc của từng thành viên theo `docs/huong-dan-chon-repo-va-pr.md`: chọn repo, lọc PR có cảnh báo mới bằng cách
A, rồi chạy B và C trên cùng tập cảnh báo.

## Phần của kien

Bốn repo: `tagbangers/wallride` (Apache-2.0), `ChukiChen/Aooms` (Apache-2.0), `ShuaiJunlan/Autumn` (GPL-2.0),
`xmomen/dms-webapp` (MIT).

| Kết quả | |
|---|---|
| PR đã đăng ký | 38 (wallride 14, aooms 10, autumn 7, dms-webapp 7). Mức nên đạt là 8–10 |
| Cảnh báo mới của A | 171 sau khi gộp trùng, 117 trong file Java. Mức nên đạt là từ 30 |
| Lượt B, C | 38/38 `ok`, 0 lỗi |
| Mô hình | `claude-sonnet-5-5` |

- Kịch bản: [03 — Lọc PR bằng A](scenarios/03-loc-pr-cach-a-kien.md), [04 — Chạy A, B, C](scenarios/04-chay-a-b-c-kien.md).
- Kết quả: [bảng đăng ký PR](results/dang-ky-pr-kien.md), [lọc A](results/loc-a-kien.md), [chạy A, B, C](results/ket-qua-abc-kien.md).
- [Người thực hiện](testers/tester-record-kien.md).

### Không có trong repo

Bảng kết quả theo PR, comment của bot, nhật ký chạy và dữ liệu thô nằm trong gói nộp qua kênh riêng của nhóm. Lý
do: repo public, và nhãn B, C theo từng cảnh báo phải ẩn với người gán nhãn.

### Cần nhóm làm tiếp

1. Chép bảng đăng ký vào bảng chung.
2. Gán nhãn chéo và mù cho 171 cảnh báo.
