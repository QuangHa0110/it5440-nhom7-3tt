# Tổng hợp lượt chạy A, B, C trên mã nguồn mở — sonnh95 và KienTranDSAI, 2026-11-25

Bản tổng hợp này gộp hai lượt chạy thử của thành viên, theo [hướng dẫn chọn repo và PR](../../docs/huong-dan-chon-repo-va-pr.md).
Đây là **lượt chạy thử quy trình**, chưa phải số liệu đánh giá: chưa có nhãn đáp án, hai người dùng hai mô hình
khác nhau và khác mô hình nhóm đã chốt (`deepseek/deepseek-v4.1-flash-1017`).

**Nguồn số liệu.**

- sonnh95: chạy `scripts/tong_hop_so_lieu.py --mu` trên gói nộp (13 file `triage-result.json`). Hồ sơ:
  PR #23, [`ket-qua-abc.md`](../../docs/test-records/2026-11-25/results/ket-qua-abc.md) sau khi merge.
- KienTranDSAI: gói nộp chưa về tới người tổng hợp, nên số liệu **chép tay** từ hồ sơ trong PR #24
  (`loc-a-kien.md`, `dang-ky-pr-kien.md`, `ket-qua-abc-kien.md`). Cần chạy lại script khi có gói.

**Giữ mù:** không ghi nhãn `likely_true` hay `likely_false` theo người, repo, PR hay cảnh báo, để người gán nhãn đáp
án không bị ảnh hưởng. Chỉ ghi số có kết luận và số không có kết luận.

## 1. Kiểm tra hợp lệ của lượt chạy

| # | Tiêu chí | sonnh95 | KienTranDSAI |
|---|---|---|---|
| V1 | Chọn PR chỉ theo A, chốt danh sách trước khi chạy B/C (P6) | Đạt | Đạt |
| V2 | Lấy mọi PR có cảnh báo mới trong một cửa sổ commit (không dùng `git blame`, không chọn theo CWE) | Đạt: 600 commit gần nhất | **Không đạt**: `git blame` từ cảnh báo còn ở HEAD |
| V3 | Mô hình và `manifest_hash` của cấu hình chung | **Không đạt**: mô hình DeepSeek suy luận riêng, `7b118a08` | **Không đạt**: `claude-sonnet-5-5` |
| V4 | Nhãn bị cắt cụt hoặc lỗi hạ tầng dưới khoảng 5% | **Không đạt**: 27/112 (24%) | Đạt: 0/346 |
| V5 | Repo thỏa R1–R5, không trùng người khác | Đạt | Đạt |
| V6 | Không luật nào quá khoảng 50% số cảnh báo (nếu quá thì báo cáo riêng) | 64% (`no-direct-response-writer`) | 61% (`unrestricted-request-mapping`) |

Hệ quả: cả hai lượt **không gộp được** thành số liệu B/C chung, và chưa dùng làm tập đánh giá chính. Phần A của
sonnh95 dùng lại được; B/C cần chạy lại với cấu hình chung. Phần A của KienTranDSAI cần chọn lại PR theo cửa sổ commit
vì `git blame` chỉ giữ cảnh báo chưa bị sửa, làm mẫu nghiêng về cảnh báo sai.

## 2. Cách A: cảnh báo mới

| Thành viên | Repo | Giấy phép | PR | Cảnh báo mới | Trong đó Java | Năm của commit |
|---|---|---|---:|---:|---:|---|
| sonnh95 | [logicaldoc/community](https://github.com/logicaldoc/community) | LGPL-3.0 | 10 | 45 | 45 | 2025–2026 |
| sonnh95 | [gentics/mesh](https://github.com/gentics/mesh) | Apache-2.0 | 3 | 11 | 7 | 2025–2026 |
| KienTranDSAI | [tagbangers/wallride](https://github.com/tagbangers/wallride) | Apache-2.0 | 14 | 91 | — | 2014–2018 (chung 4 repo) |
| KienTranDSAI | [ChukiChen/Aooms](https://github.com/ChukiChen/Aooms) | Apache-2.0 | 10 | 42 | — | 2014–2018 (chung 4 repo) |
| KienTranDSAI | [ShuaiJunlan/Autumn](https://github.com/ShuaiJunlan/Autumn) | GPL-2.0 | 7 | 28 | — | 2014–2018 (chung 4 repo) |
| KienTranDSAI | [xmomen/dms-webapp](https://github.com/xmomen/dms-webapp) | MIT | 7 | 10 | — | 2014–2018 (chung 4 repo) |
| **Tổng** | 6 repo | | **51** | **227** | | |

KienTranDSAI chỉ ghi số cảnh báo Java của cả bốn repo: 117/171. Tổng Java của hai người là 52 + 117 = 169/227.
Số cảnh báo của KienTranDSAI tính sau khi gộp trùng (173 nếu đếm theo từng PR).

**Phân bố theo luật** (mỗi người hai luật lớn nhất):

| Thành viên | Luật | Cảnh báo | Tỉ lệ trong phần của người đó |
|---|---|---:|---:|
| sonnh95 | `no-direct-response-writer` (XSS) | 36 | 64% |
| sonnh95 | `unsafe-reflection` | 7 | 13% |
| KienTranDSAI | `unrestricted-request-mapping` (CSRF, loại audit) | 105 | 61% |
| KienTranDSAI | `missing-integrity` (template HTML, không phải Java) | 38 | 22% |

## 3. Cách B và C: mức có kết luận

Mẫu số là số nhãn của từng cách (sonnh95 56, KienTranDSAI 173 theo từng PR). Không tách đúng hay sai (giữ mù).

| Thành viên | Mô hình | Cách | Có kết luận | `unknown` | Cắt cụt (`invalid`) | Lỗi cổng LLM |
|---|---|---|---:|---:|---:|---:|
| sonnh95 | DeepSeek suy luận (riêng) | B | 32 (57%) | 12 | 12 | 0 |
| sonnh95 | DeepSeek suy luận (riêng) | C | 28 (50%) | 13 | 11 | 4 |
| KienTranDSAI | `claude-sonnet-5-5`, effort `high` | B | 132 (76%) | 41 | 0 | 0 |
| KienTranDSAI | `claude-sonnet-5-5`, effort `high` | C | 130 (75%) | 43 | 0 | 0 |

Khác biệt về tỉ lệ có kết luận chủ yếu do mô hình (mô hình suy luận của sonnh95 bị cắt ở `max_tokens=1500`) và do
loại luật (luật request mapping dễ phán đoán hơn XSS trong servlet). Không so được C với B giữa hai người.

## 4. Vận hành

| Chỉ số | sonnh95 | KienTranDSAI |
|---|---|---|
| Lượt `run` | 13 (6 `ok`, 7 `degraded`) | 38 (38 `ok`) |
| Thời gian một lượt, trung vị / lớn nhất (giây) | 501 / 695 | 41 / 186 |
| Tổng thời gian (giây) | 6.048 | 2.287 |
| Độ trễ một lần gọi LLM, trung vị / lớn nhất (giây) | 8,2 / 21,2 | 8,3 / 14,3 |
| Token B và C | 428.269 | 1.108.282 (801.323 vào, 306.959 ra) |
| Máy | Máy chủ dùng chung, hai luồng song song | Không ghi |

Thời gian một lượt chủ yếu là Semgrep quét repo: repo của sonnh95 lớn hơn nhiều. Độ trễ LLM của hai mô hình gần nhau.

## 5. Việc tiếp theo

1. Nhóm gắn tag `eval-freeze-2` với mô hình chung, `max_tokens` đủ để không cắt cụt.
2. sonnh95 chạy lại B/C cho 13 PR đã đăng ký. KienTranDSAI chọn lại PR theo cửa sổ commit (có thể dùng
   `scripts/filter_prs.py` của PR #23), rồi chạy B/C với cấu hình chung.
3. Gán nhãn đáp án chéo và mù trên các cảnh báo của lượt chạy lại.
4. Chạy lại `scripts/tong_hop_so_lieu.py` trên các gói nộp để thay bản chép tay ở trên.
