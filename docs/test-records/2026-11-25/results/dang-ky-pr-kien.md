# Bảng đăng ký PR — KienTranDSAI, 2026-11-25

Danh sách 38 PR được xác định chỉ từ kết quả của cách A (P6), không thêm, bớt hay đổi theo kết quả của LLM.

## Quy tắc chọn (chỉ theo A)

1. Quét HEAD của 17 web app Java ứng viên bằng `p/default`, giữ 4 repo nhiều cảnh báo Java nhất
   (xem [loc-a-kien.md](loc-a-kien.md)).
2. Với mỗi cảnh báo tại HEAD, dùng `git blame` dòng bị báo để tìm commit đưa cảnh báo vào. Giữ commit có cha và
   thay đổi 1–1.000 dòng so với cha (P4).
3. Chạy `pr-triage run --variants none` trên cặp (cha, commit). Giữ **mọi** commit có ít nhất một cảnh báo mới trong
   file Java.

- Các commit này không gắn với PR của GitHub. Theo P2, mỗi commit là một "PR", base là commit cha. Số PR là số tự
  đặt từ 1001, theo thứ tự repo rồi SHA head.
- Ngày merge là ngày commit của SHA head.

## Bảng (hướng dẫn mục 5)

| Thành viên | Mã repo | Nguồn (OSS / cá nhân) | Giấy phép | Ngôn ngữ | Số PR hoặc SHA merge | SHA base | SHA head | Ngày merge | Số cảnh báo A |
|---|---|---|---|---|---|---|---|---|---|
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1001` / [`0ff78bf65`](https://github.com/tagbangers/wallride/commit/0ff78bf65b027bc45a9bbf6095c4ea6d02aeca09) | `e4e3e296d` | `0ff78bf65` | 2015-07-31 | 12 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1002` / [`15a464495`](https://github.com/tagbangers/wallride/commit/15a464495fbac542343f75c4a575a3427ff68eba) | `d1f40369f` | `15a464495` | 2014-11-23 | 3 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1003` / [`372764bac`](https://github.com/tagbangers/wallride/commit/372764bac6a6c9aba4a8f15caf338ad6ef16195c) | `ab0af512e` | `372764bac` | 2014-05-05 | 4 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1004` / [`5ceedb3c8`](https://github.com/tagbangers/wallride/commit/5ceedb3c84dde58dac5f20ee74bfdbd4e842de9d) | `7a7f6bbed` | `5ceedb3c8` | 2014-05-04 | 6 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1005` / [`5dbcb5952`](https://github.com/tagbangers/wallride/commit/5dbcb5952443e7d621c55edea96009bce37c2d16) | `bce96fb65` | `5dbcb5952` | 2017-03-04 | 12 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1006` / [`716c728a9`](https://github.com/tagbangers/wallride/commit/716c728a9a77d29ae2db1a48ef3ecff479179f01) | `2e75681ae` | `716c728a9` | 2014-11-04 | 15 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1007` / [`7cd7c9c72`](https://github.com/tagbangers/wallride/commit/7cd7c9c7269e127c9a1f3dc8f565e8dd5c4d7e81) | `95776c9de` | `7cd7c9c72` | 2014-08-22 | 6 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1008` / [`832fa05aa`](https://github.com/tagbangers/wallride/commit/832fa05aa77ee31295988d7f447c6c470c0341ab) | `2fe44486c` | `832fa05aa` | 2014-09-25 | 6 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1009` / [`95776c9de`](https://github.com/tagbangers/wallride/commit/95776c9de40bc9aa25b07dc59b3bd1724e8ff6e3) | `b4ae90374` | `95776c9de` | 2014-08-22 | 4 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1010` / [`9a40fda2f`](https://github.com/tagbangers/wallride/commit/9a40fda2f42a8e920ede052a81c144aa4e3f4207) | `ac767b3c9` | `9a40fda2f` | 2014-11-17 | 4 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1011` / [`ac767b3c9`](https://github.com/tagbangers/wallride/commit/ac767b3c9ffb226eef54bd14646ffab35accfaf7) | `e167672ae` | `ac767b3c9` | 2014-11-10 | 10 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1012` / [`dad4382b0`](https://github.com/tagbangers/wallride/commit/dad4382b063a1d0e22aefd4696fd50dd13104e5a) | `c2b42fbb6` | `dad4382b0` | 2014-05-05 | 3 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1013` / [`dc6c49a2b`](https://github.com/tagbangers/wallride/commit/dc6c49a2b8f2966ed2b428118558e90fd19ca567) | `c71266ca3` | `dc6c49a2b` | 2014-08-24 | 1 |
| KienTranDSAI | `wallride` | OSS ([tagbangers/wallride](https://github.com/tagbangers/wallride)) | Apache-2.0 | Java | `1014` / [`f0e9347fc`](https://github.com/tagbangers/wallride/commit/f0e9347fcbf26d555ff08ee9e848b93f22540b62) | `26b0084b3` | `f0e9347fc` | 2014-05-06 | 5 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1015` / [`027ebb068`](https://github.com/ChukiChen/Aooms/commit/027ebb0684ea4d594f4c105f1cb95e2a7d068b97) | `c73fa713f` | `027ebb068` | 2018-09-13 | 11 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1016` / [`515cb7f36`](https://github.com/ChukiChen/Aooms/commit/515cb7f36d79b38f2e3bd7889fb8ffc3c2291ee7) | `c33e22583` | `515cb7f36` | 2018-11-08 | 1 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1017` / [`667957f74`](https://github.com/ChukiChen/Aooms/commit/667957f747b8604bb70338820bcddbb8eeca0770) | `0a527fca9` | `667957f74` | 2018-11-11 | 1 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1018` / [`765fa0f33`](https://github.com/ChukiChen/Aooms/commit/765fa0f331eb9ca4057951967315ab72f562f795) | `11055f377` | `765fa0f33` | 2018-11-07 | 1 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1019` / [`9022dc022`](https://github.com/ChukiChen/Aooms/commit/9022dc022d3fed212739ecc1522fbeab97e132f5) | `bee903c57` | `9022dc022` | 2018-09-13 | 4 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1020` / [`90503ac8c`](https://github.com/ChukiChen/Aooms/commit/90503ac8c4ddb6f9eed6f802c57d5cee983edabd) | `124857a90` | `90503ac8c` | 2018-09-17 | 9 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1021` / [`a51ec7718`](https://github.com/ChukiChen/Aooms/commit/a51ec7718c576c63f778fcbb0ae4c9b2f923ab44) | `246351037` | `a51ec7718` | 2018-09-18 | 12 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1022` / [`b40dd53f0`](https://github.com/ChukiChen/Aooms/commit/b40dd53f0d80c2b4f65319d64eccee1f5aa005d2) | `eccf3cc3b` | `b40dd53f0` | 2018-11-12 | 1 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1023` / [`c33e22583`](https://github.com/ChukiChen/Aooms/commit/c33e22583805127bd4474549f3b477da3564d331) | `c90486d7d` | `c33e22583` | 2018-11-08 | 1 |
| KienTranDSAI | `aooms` | OSS ([ChukiChen/Aooms](https://github.com/ChukiChen/Aooms)) | Apache-2.0 | Java | `1024` / [`d54099a3f`](https://github.com/ChukiChen/Aooms/commit/d54099a3f11a8d8d6e0d75fc9d67a696bec5e107) | `9e34148f1` | `d54099a3f` | 2018-10-08 | 1 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1025` / [`0356e3ae9`](https://github.com/ShuaiJunlan/Autumn/commit/0356e3ae986a420296a375f81667212537d4b4e6) | `330233143` | `0356e3ae9` | 2018-04-10 | 3 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1026` / [`0e659f4b5`](https://github.com/ShuaiJunlan/Autumn/commit/0e659f4b564572c1289581f49e74b98deebdad3b) | `b71f6b47e` | `0e659f4b5` | 2018-04-16 | 13 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1027` / [`6baade696`](https://github.com/ShuaiJunlan/Autumn/commit/6baade6967a85d84146fd6308296b4dd9f5ed4a7) | `622ab5152` | `6baade696` | 2017-11-27 | 6 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1028` / [`96daf17ff`](https://github.com/ShuaiJunlan/Autumn/commit/96daf17ffa76bd0b91070977b077c76b3ba7af85) | `f7ca915e1` | `96daf17ff` | 2017-12-04 | 3 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1029` / [`9c9c6e619`](https://github.com/ShuaiJunlan/Autumn/commit/9c9c6e6196df4843e240b7d24912b4b1fc6680e4) | `6fa312577` | `9c9c6e619` | 2017-11-07 | 2 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1030` / [`b1289a4f9`](https://github.com/ShuaiJunlan/Autumn/commit/b1289a4f99688ce1764b69a538b714421ab118b3) | `3f17710d2` | `b1289a4f9` | 2017-11-05 | 1 |
| KienTranDSAI | `autumn` | OSS ([ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn)) | GPL-2.0 | Java | `1031` / [`dedd13778`](https://github.com/ShuaiJunlan/Autumn/commit/dedd13778469c856c93b685cfebfe4395a80ede1) | `93f878c22` | `dedd13778` | 2018-04-11 | 2 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1032` / [`2c2bd1175`](https://github.com/xmomen/dms-webapp/commit/2c2bd1175f56e145fc5601e3a5dfc81c8b7723b1) | `ef21d1133` | `2c2bd1175` | 2016-08-09 | 1 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1033` / [`5326e3a43`](https://github.com/xmomen/dms-webapp/commit/5326e3a439feeabba7e8f1c43e226dbd1215e5af) | `6023cd2f3` | `5326e3a43` | 2017-03-28 | 2 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1034` / [`858461b06`](https://github.com/xmomen/dms-webapp/commit/858461b067f30d2789c2becc55e55cc53b7db25f) | `ab3bf275b` | `858461b06` | 2017-06-07 | 1 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1035` / [`a335d213a`](https://github.com/xmomen/dms-webapp/commit/a335d213a72eb870db75b8669cb4e639021bdcbe) | `41892867e` | `a335d213a` | 2017-05-25 | 1 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1036` / [`ae153924d`](https://github.com/xmomen/dms-webapp/commit/ae153924d249f5ed1bacbf5b253829958daff451) | `bfb734b37` | `ae153924d` | 2016-05-21 | 2 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1037` / [`bba0cc947`](https://github.com/xmomen/dms-webapp/commit/bba0cc947cadc636286a3500b9cf0a5ffeb1ee09) | `1b401c98b` | `bba0cc947` | 2017-04-25 | 2 |
| KienTranDSAI | `dms-webapp` | OSS ([xmomen/dms-webapp](https://github.com/xmomen/dms-webapp)) | MIT | Java | `1038` / [`f0c07048c`](https://github.com/xmomen/dms-webapp/commit/f0c07048c9e2e84abd5508429817a4cafd1ad0a6) | `459f9be4f` | `f0c07048c` | 2016-03-19 | 1 |

**Tổng:** 38 PR, 173 cảnh báo mới của A (171 sau khi gộp trùng), trong đó 117 nằm trong file Java.

| Mã repo | PR | Cảnh báo mới |
|---|---|---|
| `wallride` | 14 | 91 |
| `aooms` | 10 | 42 |
| `autumn` | 7 | 28 |
| `dms-webapp` | 7 | 10 |

Các số trong bảng trên tính sau khi gộp trùng.

Phân bố: 120/171 cảnh báo là CWE-352 (chủ yếu `unrestricted-request-mapping`, 105), 38 là `missing-integrity` trong
template Thymeleaf của wallride. Không trùng repo với bảng của sonnh (`logicaldoc`, `mesh`).
