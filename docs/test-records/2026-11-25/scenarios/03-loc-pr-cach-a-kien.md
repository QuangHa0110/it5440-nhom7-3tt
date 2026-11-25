# Kịch bản 03 — Lọc PR bằng A trên repo Java mã nguồn mở (kien)

| Trường | Nội dung |
|---|---|
| Mục tiêu | Tìm ít nhất 5 PR (nên đạt 8–10) có tổng ít nhất 20 cảnh báo mới (nên đạt từ 30) của cách A trong mã Java, theo bước 3 của `docs/huong-dan-chon-repo-va-pr.md` |
| Repo | `wallride` = [tagbangers/wallride](https://github.com/tagbangers/wallride) (Apache-2.0), `aooms` = [ChukiChen/Aooms](https://github.com/ChukiChen/Aooms) (Apache-2.0), `autumn` = [ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn) (GPL-2.0), `dms-webapp` = [xmomen/dms-webapp](https://github.com/xmomen/dms-webapp) (MIT) |
| Tiền điều kiện | `make setup`. `scripts/fetch_semgrep_rules.py --frozen` tải `p/default` khớp `rulesets.lock`. Repo clone vào `data/raw/` |
| Cách làm | Quét HEAD nhiều ứng viên, dùng `git blame` để tìm commit đưa cảnh báo vào, rồi chạy `pr-triage run --variants none` trên cặp (cha, commit) |
| Kết quả mong đợi | Bảng đăng ký có SHA base, head, ngày và số cảnh báo A; danh sách chỉ dựa trên A |
| Ngoài phạm vi | Chạy B, C (kịch bản 04). Gán nhãn |

## Thực hiện và kết quả

Chi tiết: [lọc A](../results/loc-a-kien.md), [bảng đăng ký](../results/dang-ky-pr-kien.md).

| Mong đợi | Thực tế | Đạt |
|---|---|---|
| Ít nhất 5 PR có cảnh báo mới trong mã Java | 38 PR trên 4 repo | Có |
| Ít nhất 20 cảnh báo mới | 171 cảnh báo, 117 trong file Java | Có |
| Danh sách chỉ dựa trên A | Chọn mọi commit có cảnh báo Java mới trong tập ứng viên | Có |
