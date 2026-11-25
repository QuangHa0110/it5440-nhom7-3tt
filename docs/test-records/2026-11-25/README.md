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

## Gói dữ liệu (bước 7 của hướng dẫn)

[Google Drive](https://drive.google.com/drive/folders/1Rm-urWEeJCj1Lv2mUXul-8_26AFWD2MV?usp=sharing), ai có link đều xem và tải được. Gồm SQLite, `triage-result.json` của 13 PR, tư liệu từng repo (`loc-a.tsv`,
`ket-qua.tsv`, `thong-tin-repo.md`, `nhat-ky.md`, comment, ảnh), ca điển hình và log. Có hai bản nén (đầy đủ 7 MB,
gọn 0,5 MB chỉ phần bắt buộc) và thư mục `giai-nen/` để xem trực tiếp. Giá trị `_auth=` của `.npmrc` (TD-9) và tên
model của cổng LLM đã được che.

Để giữ mù, người gán nhãn dùng phiếu từ `pr-triage eval label-export`, không mở `*-run/`, `comment/` hay
`ca-dien-hinh.md` trước khi gán xong.

## Bước tiếp theo

Gán nhãn chéo và mù cho 56 cảnh báo. Repo không trùng với thành viên khác (chưa ai khác đăng ký).
