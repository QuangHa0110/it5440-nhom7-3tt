# Bảng đăng ký PR — trinq

Mỗi dòng là một merge commit hoặc commit trên nhánh chính (P2). Cột "Java" là số cảnh báo nằm trong file `.java`.

| Repo | Số PR | SHA base | SHA head | Ngày | Cảnh báo A | Java |
|---|---|---|---|---|---|---|
| hmcts/document-management-store-app | #3083 | `3f5afed7e4a678d3d8dc7b9ad6074123c0dbb64d` | `433708343645abeb272344638f664f15fa41dbfd` | 2026-02-10 | 1 | 0 |
| hmcts/document-management-store-app | #1760 | `225c28bd988a82b89bb1286ba5cc9ba280e9a168` | `9ca6d95a284da4722ae21674d679c2c61d3781e4` | 2023-06-08 | 1 | 1 |
| hmcts/document-management-store-app | #1419 | `583c42e71a175482be38c90e93427ecc79627db2` | `cd1bf47e598dfd61676816883a9dd4f496650cb9` | 2022-08-30 | 1 | 0 |
| hmcts/document-management-store-app | #1380 | `b33cffce01eeeeaafb7a694855987ea52cc02a68` | `138e9c9346cde1721c1d7b7605307cbe124ef57a` | 2022-06-13 | 1 | 1 |
| hmcts/document-management-store-app | #578 | `cffc0cd1e0703d0319ef48fc11c1b8794f588485` | `ab9ce385ebc4b2ef4839cb0998f34cdf2685230a` | 2020-06-05 | 1 | 1 |
| hmcts/document-management-store-app | #537 | `b9e7f49820315646c3974d01c0c533717b073761` | `3455130b244a0a5ced1517b40eb7a03c9a348e9b` | 2020-03-24 | 1 | 0 |
| hmcts/document-management-store-app | #527 | `2971f1582f2ce9228db12d3edbb6f70df7ef8a55` | `037b5f9d5268e3122723f2b833c5e1c6502b816a` | 2020-03-03 | 1 | 1 |
| hmcts/document-management-store-app | không có | `0a1aa00ad3b74d47c8f4185807d0acf31dbb19e4` | `19698c8c844cdbd4c15350692edc7bc953f7a9c2` | 2019-07-30 | 7 | 1 |
| hmcts/document-management-store-app | #61 | `8a4ac37bb5b76e1187d6d8dff357242dc1ae86d3` | `ea0d54912a1206edb49d344c1160b17f3e67f252` | 2018-04-11 | 2 | 0 |
| hmcts/document-management-store-app | #43 | `4cf64808fc0776c8d7024134296903c62a689e15` | `c74c9066b62634c2d03da9dfbf52c912ca8adb41` | 2018-03-02 | 6 | 0 |
| hmcts/document-management-store-app | #35 | `d84f79ac7c7f87432b75df9d56c930bfb9946248` | `c47669603d6466870e66bd3aad1e797b2fe60959` | 2018-02-15 | 7 | 0 |
| hmcts/document-management-store-app | #25 | `2f94b0bb9fc7b84dc5bbbe8276fa5277a420b512` | `3924b0a397530ea08bac85ee02bd81f461f3c03f` | 2018-02-02 | 1 | 1 |
| hmcts/document-management-store-app | #22 | `bd36e42eafa83151e27371a2b134ff2d3199b294` | `0e18ecb49ae3427a01849d45437a2cede1b4c268` | 2018-01-25 | 1 | 0 |
| informatici/openhospital-core | #1166 | `190033caada4fd17e5ff9e1ab42219aed5167de9` | `05b6b2c7ed8c55b83643ab1691c3305f735e497f` | 2023-11-24 | 4 | 0 |
| informatici/openhospital-core | #1167 | `f0f735473fea6ad7e70841e6e953969fbe696830` | `09a9ecd093283d5484e23d86953d0c2147080518` | 2024-01-25 | 1 | 0 |
| informatici/openhospital-core | #712 | `7361a3b1c9acd55e511b9e95ff48bb72dc2a3365` | `0e7e58c74630100163608f45460127e4c6633211` | 2022-07-27 | 4 | 4 |
| informatici/openhospital-core | #56 | `936ebb2f93ea8e1eb37d025b5adabc447d916fae` | `3d3d34ae83abf5405024fa46928f681fd68160d3` | 2020-03-07 | 1 | 1 |
| informatici/openhospital-core | #1002 | `74db71987958b3afab38845ffc30f27a8f69fdf6` | `c749346cf0718f93113ac2bb057204b79b808996` | 2023-05-30 | 2 | 0 |
| informatici/openhospital-core | #91 | `e9571421a7ef42174622b677d1a2b6539a0943fa` | `1590748d851c623730f4bfe1b2f9af4525374642` | 2020-06-14 | 1 | 1 |
| **Tổng** | 19 PR | | | | **44** | **12** |

**Loại khỏi danh sách (4 ứng viên), theo tiêu chí không dựa vào nhãn LLM:**

| Commit | Lý do |
|---|---|
| hmcts `75435960` | 4.511 dòng thay đổi, vượt P4 |
| hmcts `d664f967` | 1.297 dòng, vượt P4 |
| hmcts `6c32353b` | commit "merge master", không phải một PR |
| openhospital `cf6f0a25` | 8.656 dòng, vượt P4 |

Cần nhóm xem lại: openhospital `09a9ecd0` là PR nâng Java 17 (P3 loại PR chỉ đổi phiên bản; PR này có sửa file Java).
Người chốt danh sách đã thấy bảng tóm tắt B/C của lượt lọc trước khi loại 4 ứng viên (lệch P6 và bước 4).
