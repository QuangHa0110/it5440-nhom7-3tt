# 2026-11-25 — Lọc PR bằng A và chạy A, B, C trên hai repo Java mã nguồn mở

Thực hiện phần việc của một thành viên theo `docs/huong-dan-chon-repo-va-pr.md`: chọn repo, lọc PR có cảnh báo mới
bằng cách A, chốt bảng đăng ký trước khi chạy B và C (P6), rồi chạy A, B, C bằng tham số chung. Hai repo:
`logicaldoc/community` (LGPL-3.0) và `gentics/mesh` (Apache-2.0). Kế hoạch: P17
(`docs/plans/done/2026-11-25-p17-thu-du-lieu-oss-sonnh.md`).

| Kết quả | |
|---|---|
| PR đã đăng ký | 13 (logicaldoc 10, mesh 3), mức nên đạt của hướng dẫn là 8–10 |
| Cảnh báo mới của A | 56 (logicaldoc 45, mesh 11), mức nên đạt là ít nhất 30 |
| Lượt B, C | 13/13 xong, 6 `ok`, 7 `degraded` |
| Nhãn đáp án | Chưa gán, chờ gán chéo và mù |

## Hồ sơ

- Kịch bản: [01 — Lọc PR bằng A](scenarios/01-loc-pr-cach-a.md), [02 — Chạy A, B, C](scenarios/02-chay-a-b-c.md).
- Kết quả: [bảng đăng ký PR](results/dang-ky-pr.md), [lọc A](results/loc-a.md), [chạy A, B, C](results/ket-qua-abc.md).
- [Người thực hiện](testers/tester-record.md).

## Không có trong repo

Bảng kết quả theo PR, comment của bot, ảnh, ca điển hình, nhật ký chạy và dữ liệu thô nằm trong gói nộp qua kênh
riêng của nhóm. Lý do: repo public, và nhãn B, C theo từng cảnh báo phải ẩn với người gán nhãn đến khi gán xong.

## Cần nhóm làm tiếp

1. Chép bảng đăng ký vào bảng chung và kiểm tra không trùng repo với thành viên khác.
2. Gán nhãn chéo và mù cho 56 cảnh báo.
3. Quyết định có chạy lại B, C bằng mô hình đã khóa và `max_tokens` lớn hơn không (xem giới hạn 1–2 trong
   [kết quả](results/ket-qua-abc.md)).
