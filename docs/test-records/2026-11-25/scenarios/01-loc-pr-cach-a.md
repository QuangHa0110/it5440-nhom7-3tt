# Kịch bản 01 — Lọc PR bằng cách A trên hai repo Java mã nguồn mở

| Trường | Nội dung |
|---|---|
| Mục tiêu | Chọn các PR có ít nhất một cảnh báo mới của A (P1) trên logicaldoc/community và gentics/mesh, đạt chỉ tiêu mỗi thành viên: ≥ 5 PR, ≥ 20 cảnh báo mới (nên đạt 8–10 PR, ≥ 30). |
| Repo | `logicaldoc` = [logicaldoc/community](https://github.com/logicaldoc/community) (LGPL-3.0), `mesh` = [gentics/mesh](https://github.com/gentics/mesh) (Apache-2.0) |
| Tiền điều kiện | Bộ luật `p/default` tải bằng `scripts/fetch_semgrep_rules.py --frozen`, khớp mã băm trong `configs/semgrep/rulesets.lock`. Semgrep CE 1.185.0. Không gọi LLM. |
| Cách chạy | `scripts/filter_prs.py prefilter` trên N commit first-parent gần nhất, rồi `scripts/filter_prs.py replay --variants none --no-secrets` trên các ứng viên (tham số giống `pr-triage replay`). Chỉ xét commit có 1–1.000 dòng Java thay đổi so với merge-base (P3, P4). |
| Kết quả mong đợi | Mỗi ứng viên có `replay-<sha>-merged.json` với `status: ok`. Ở các commit có cả hai tầng, số cảnh báo của bộ sàng không nhỏ hơn số của pipeline. Danh sách PR được chốt và ghi vào [bảng đăng ký](../results/dang-ky-pr.md) **trước** khi chạy B, C (P6). |

## Thực hiện và kết quả

Xem [kết quả lọc A](../results/loc-a.md).

- Tầng 1 chạy trên 600 commit first-parent của mesh và 1.500 commit của logicaldoc. Tầng 2 chạy trên các ứng viên
  nằm trong 600 commit gần nhất. Mọi lượt tầng 2 trên ứng viên có `status: ok`.
- Có 13 PR với 56 cảnh báo mới (logicaldoc 10 / 45, mesh 3 / 11), vượt mức "nên đạt". Danh sách được chốt ở
  commit `6b65826` lúc 2026-11-25 13:25:57 (+07), trước lượt B, C đầu tiên lúc 13:26:32.
- Ở mọi commit có kết quả cả hai tầng, số cảnh báo của tầng 1 không nhỏ hơn số của tầng 2. Có 22/25 commit khớp
  đúng danh sách `finding_id`.
- Phát sinh: bản đầu của tầng 1 bỏ sót ứng viên vì Semgrep CE trả `"requires login"` ở `extra.lines`. Đã sửa
  trước khi chốt danh sách.

**Kết luận:** Đạt.
