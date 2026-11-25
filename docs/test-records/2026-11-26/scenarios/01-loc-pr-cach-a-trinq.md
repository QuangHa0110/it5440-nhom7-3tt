# Kịch bản 01 — Lọc PR bằng A trên hai repo (trinq)

**Mục tiêu:** tìm PR có ít nhất một cảnh báo mới của A, theo [hướng dẫn](../../../huong-dan-chon-repo-va-pr.md) mục 2 và 3.

**Repo:** `hmcts/document-management-store-app` (MIT) và `informatici/openhospital-core` (GPL-3.0). Java là ngôn ngữ chính, dưới 1.000 sao, không thuộc danh sách loại trừ, không trùng repo của #23 và #24.

**Tiền điều kiện:** tag `v0.1.0`, bộ luật `p/default` khớp `rulesets.lock`.

**Cách làm:** `scripts/filter_prs.py` (đang ở #23, chưa merge): `prefilter` trên các commit first-parent sửa file Java, rồi `replay` đầy đủ trên ứng viên.

**Kết quả mong đợi:** ít nhất 5 PR và 20 cảnh báo mới.

**Kết quả thực tế:** đạt, xem [loc-a-trinq.md](../results/loc-a-trinq.md). Một điểm lệch: bước `replay` của script chạy cả B và C (bán kính 10, hiển thị B) trước khi chốt danh sách. Kết quả lượt đó không dùng làm số đo.
