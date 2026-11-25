# Lọc PR bằng A — trinq, 2026-11-25

Kịch bản: [01](../scenarios/01-loc-pr-cach-a-trinq.md).

| | hmcts | openhospital |
|---|---|---|
| Commit first-parent quét ngược (tối đa) | 4.800 | 3.000 |
| Commit sửa Java | 320 | 709 |
| Ứng viên sau tầng 1 | 16 (45 cảnh báo có thể mới) | 10 (24 cảnh báo có thể mới) |
| Commit có cảnh báo mới sau `replay` | 16 (45 cảnh báo) | 7 (15 cảnh báo) |
| Loại theo tiêu chí | 3 (14 cảnh báo) | 1 (2 cảnh báo) |
| **Chốt** | **13 PR, 31 cảnh báo** | **6 PR, 13 cảnh báo** |

Phần lớn lịch sử gần đây của hmcts là commit nâng thư viện tự động, nên nhiều PR được chọn thuộc giai đoạn 2018 đến 2020.
