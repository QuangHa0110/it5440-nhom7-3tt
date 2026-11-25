# Bảng đăng ký PR — sonnh95, chốt 2026-11-25 13:25 (+07)

Chốt **trước** khi chạy B và C (P6). Commit chứa file này là mốc thời gian. Sau mốc này không thêm, bớt hay đổi PR
theo kết quả của LLM.

## Quy tắc chọn (chỉ theo A)

Chọn **mọi** commit first-parent có ít nhất một cảnh báo mới của A (`status: ok`) trong **600 commit first-parent
gần nhất** của nhánh đã clone. Hai repo dùng cùng một quy tắc, không chọn tay từng PR.

| Mã repo | Nhánh, đỉnh lúc clone | Cửa sổ 600 commit | Commit sửa 1–1.000 dòng Java (P3, P4) |
|---|---|---|---|
| `logicaldoc` | `master` @ `aaa5bf657` (2026-11-24) | 2025-10-13 → 2026-11-24 | 456 |
| `mesh` | `dev` @ `9bff412cd` (2026-11-17) | 2021-11-11 → 2026-11-17 | 260 |

- Repo không dùng PR của GitHub cho các commit này (logicaldoc commit thẳng lên `master`, mesh merge nhánh hotfix).
  Theo P2, mỗi commit first-parent là một "PR". Số PR là số âm `-i` do `replay` gán (vị trí thứ `i` trong danh
  sách first-parent), kèm SHA của commit merge.
- SHA base là merge-base mà pipeline dùng (`result.run.base_sha`). SHA head là đỉnh nhánh được merge, hoặc chính
  commit nếu đó là commit thẳng. Ngày merge là ngày commit của commit first-parent.
- Kiểm P3 bằng tiêu đề và diff: mọi commit dưới đây đều sửa mã Java thật, không có commit nào chỉ sửa tài liệu,
  bump phiên bản hay định dạng lại mã.

## Bảng (hướng dẫn mục 5)

| Thành viên | Mã repo | Nguồn (OSS / cá nhân) | Giấy phép | Ngôn ngữ | Số PR hoặc SHA merge | SHA base | SHA head | Ngày merge | Số cảnh báo A |
|---|---|---|---|---|---|---|---|---|---|
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-13` / [`b51c15c4b`](https://github.com/logicaldoc/community/commit/b51c15c4b6b57b8c90d57d70ff6eff68970af4f8) | `6ea50f957` | `b51c15c4b` | 2026-10-30 | 2 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-46` / [`3163eca7a`](https://github.com/logicaldoc/community/commit/3163eca7a5f5c0033a7a505dc28846c54da28d52) | `99703ccf5` | `3163eca7a` | 2026-09-28 | 2 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-284` / [`a18e32a0d`](https://github.com/logicaldoc/community/commit/a18e32a0d099da52f5ce36b3e27cffce59f37026) | `70a6118e8` | `a18e32a0d` | 2026-03-31 | 5 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-304` / [`8237b759c`](https://github.com/logicaldoc/community/commit/8237b759c4fb1bbabc568a199ffe8e95aac0cbc3) | `2f029b0ba` | `8237b759c` | 2026-03-12 | 7 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-306` / [`205c079b0`](https://github.com/logicaldoc/community/commit/205c079b05802b6cab1807fe7faa43541f723107) | `43d423076` | `205c079b0` | 2026-03-11 | 22 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-362` / [`859ec580f`](https://github.com/logicaldoc/community/commit/859ec580f1c6a090ac870625064b276062d9d7ae) | `59c3ffa2b` | `859ec580f` | 2026-02-11 | 1 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-387` / [`3293b924b`](https://github.com/logicaldoc/community/commit/3293b924b9742656efbadcca9a5e90c30c43cef4) | `ea4a6cf75` | `3293b924b` | 2026-01-27 | 2 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-395` / [`3e3c53929`](https://github.com/logicaldoc/community/commit/3e3c5392989d9abbf128d2844b3f63ec46e43b08) | `6ceca60a1` | `3e3c53929` | 2026-01-16 | 1 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-538` / [`77429a004`](https://github.com/logicaldoc/community/commit/77429a004442a5a5b9281420661e6ef5ae3f7808) | `f985419c8` | `77429a004` | 2025-11-14 | 2 |
| sonnh95 | `logicaldoc` | OSS ([logicaldoc/community](https://github.com/logicaldoc/community)) | LGPL-3.0 | Java | `-555` / [`c9558a14f`](https://github.com/logicaldoc/community/commit/c9558a14f8222215812d9e208e917524ea14ffef) | `b8006bc3e` | `c9558a14f` | 2025-11-07 | 1 |
| sonnh95 | `mesh` | OSS ([gentics/mesh](https://github.com/gentics/mesh)) | Apache-2.0 | Java | `-87` / [`95c043b02`](https://github.com/gentics/mesh/commit/95c043b02c362669d0d409a1aca7b0a3aa3872a4) | `f244e4e69` | `5c36969fb` | 2026-07-10 | 1 |
| sonnh95 | `mesh` | OSS ([gentics/mesh](https://github.com/gentics/mesh)) | Apache-2.0 | Java | `-152` / [`a5ec4af4e`](https://github.com/gentics/mesh/commit/a5ec4af4e1292b8b5af5f3c76266fdd67a2318c4) | `2d05c5b6a` | `e8d3a897c` | 2025-10-06 | 2 |
| sonnh95 | `mesh` | OSS ([gentics/mesh](https://github.com/gentics/mesh)) | Apache-2.0 | Java | `-190` / [`8d2bd4d4d`](https://github.com/gentics/mesh/commit/8d2bd4d4d753513e9c915468a1ab73b74d472b26) | `e35d622ed` | `fe2e0f426` | 2025-05-08 | 8 |

**Tổng:** 13 PR, 56 cảnh báo mới của A (logicaldoc 10 PR / 45, mesh 3 PR / 11). Chỉ tiêu: tối thiểu 5 PR / 20
cảnh báo, nên đạt 8–10 PR / ≥ 30 cảnh báo.

Ghi chú để người tổng hợp và người gán nhãn biết trước:

- PR `logicaldoc -306` một mình có 22 cảnh báo, cùng luật `no-direct-response-writer`, trong các servlet dữ liệu
  (`ContactsDataServlet`, `AttributeOptionsDataServlet`, ...). Commit đổi `writer.print("<id>" + x + "</id>")`
  thành `writer.print(String.format("<id>%d</id>", x))`. Đoạn mã ở dòng bị báo đổi nên dấu vân tay đổi, và
  pipeline coi các cảnh báo này là mới dù luồng dữ liệu không đổi. PR `-284` và `-304` có cùng kiểu thay đổi.
- PR `mesh -190` có 4 cảnh báo ngoài Java, trong `js/.npmrc` (3 `detected-npm-registry-auth-token`, 1
  `npm-missing-minimum-release-age`). File này đang công khai trên repo gốc. Tư liệu không chép lại giá trị.
