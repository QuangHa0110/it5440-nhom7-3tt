# P17. Thu dữ liệu A, B, C trên repo Java mã nguồn mở — phần của sonnh

- **Status:** active
- **Người làm:** sonnh (với Claude Code)
- **Đóng:** phần việc của một thành viên trong [hướng dẫn chọn repo và PR](../../huong-dan-chon-repo-va-pr.md)
- **Quyết định cho phép:** hướng dẫn chọn repo và PR (PR #21), proposal mục 8.3 (phương án dự phòng)
- **Nhánh:** `sonnh/eval/chon-repo-pr`
- **Bắt đầu / Kết thúc:** 2026-11-25 / —

---

## Bối cảnh

Chưa chạy được trên mã của công ty, nên mỗi thành viên tự chọn repo Java mã nguồn mở, lọc PR bằng cách A,
chạy B và C, rồi nộp dữ liệu cho người tổng hợp. Chỉ tiêu mỗi người: ít nhất 5 PR có cảnh báo mới và 20 cảnh báo
mới (nên đạt 8–10 PR, từ 30 cảnh báo).

## Ngoài phạm vi

- Không gán nhãn (mục 6 của hướng dẫn: gán chéo, mù, do người). Không dùng AI để gán nhãn đáp án.
- Không đăng comment lên PR của repo gốc mã nguồn mở. Đăng thử trên fork là tùy chọn, chưa làm.
- Không commit dữ liệu thô (mã của repo được quét, JSON kết quả, SQLite, ảnh thô). Các thứ này nộp qua kênh
  riêng của nhóm (hướng dẫn mục 7, 8).
- Không đổi tham số B/C hay prompt của nhóm.

## Hiện trạng đã kiểm chứng

- 2026-11-25: `main` = `dev` = `f31331f`/`81929df` (cùng nội dung). `scripts/fetch_semgrep_rules.py --frozen` tải
  `p/default` khớp sha256 trong `configs/semgrep/rulesets.lock` (1074 luật).
- Khảo sát 15 repo Java ứng viên (quét HEAD bằng `p/default`, đếm cảnh báo trên file Java): nhiều nhất là
  logicaldoc/community (104), gentics/mesh (74), jivejdon (31). Các repo còn lại dưới 20.
- Một lượt `pr-triage replay` trên repo vài trăm nghìn dòng mất 3–10 phút mỗi commit khi máy bận, và phần lớn
  commit không sinh cảnh báo mới. Ở 10 commit đầu tiên chạy bằng pipeline đầy đủ, không commit nào có cảnh báo mới.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | Kế hoạch này | File nằm ở `docs/plans/active/` | — |
| T2 | Script lọc PR hai tầng: sàng sơ bộ theo file thay đổi, rồi chạy pipeline đầy đủ trên ứng viên | `scripts/filter_prs.py` có test, `make check` qua; trên mesh, 7 commit chạy pipeline đầy đủ cho 0 cảnh báo mới thì bộ sàng cũng cho 0 | T1 |
| T3 | Lọc A, chốt và đăng ký danh sách PR trước khi chạy B, C (P6) | Bảng đăng ký trong hồ sơ test có SHA base/head, ngày merge, số cảnh báo A; tổng ≥ 5 PR và ≥ 20 cảnh báo | T2 |
| T4 | Chạy A, B, C trên các PR đã chốt bằng tham số chung | Mọi PR có `triage-result.json`, không lượt nào `failed`; bảng tổng hợp số nhãn B/C mỗi PR | T3 |
| T5 | Hồ sơ test và devlog | `docs/test-records/2026-11-25/` theo quy ước; devlog ghi các điều bất ngờ | T4 |
| T6 | Đóng kế hoạch | File chuyển sang `done/` bằng `git mv`, có mục Kết quả | T5 |

## Cổng

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì khi xảy ra |
|---|---|---|
| `p/default` báo quá ít cảnh báo trên repo OSS, không đủ chỉ tiêu | Lọc A cho dưới 20 cảnh báo | Sàng thêm lịch sử cũ hơn hoặc thêm repo thứ ba; không chọn theo kết quả B/C |
| Mô hình LLM dùng khác model nhóm đã khóa ở `eval-freeze-1` | Manifest của lượt chạy khác `configs/eval/manifest.json` | Ghi rõ trong nhật ký nộp kèm; nếu nhóm chốt model khác thì chạy lại B/C, phần A giữ nguyên |
| Trùng repo với thành viên khác | Bảng đăng ký chung có repo trùng | Báo nhóm trước khi người tổng hợp gộp dữ liệu |

---

## Kết quả

*Điền khi đóng kế hoạch. Không sửa phần thân phía trên.*

- **Kết quả:**
- **Khác kế hoạch ở đâu:**
- **Ghi ở:** devlog, mục nợ, ADR
