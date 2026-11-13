# P10. Vai trò phản hồi, CC, check run, làm sạch nội dung

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0014, ADR 0012 D6
- **Nhánh:** `trinq/bot/roles-cc-checks`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Kịch bản outsource cần phân biệt tác giả với người review, CC đúng người, chú thích theo dòng, và nội dung do mô hình sinh không được gây nhiễu.

## Ngoài phạm vi

Không có comment theo dòng kiểu review. Dùng chú thích của check run.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | Thêm vai trò vào `Reply`, `FeedbackEvent`, `PrRef.author` | Test serde và kho | — |
| T2 | `resolve_states` theo `trusted_roles` | Test: `fp` của tác giả không làm thành MARKED_FALSE khi chỉ tin reviewer | T1 |
| T3 | Làm sạch markdown: vô hiệu `@`, thoát HTML, cắt độ dài | Test: giải thích chứa `@user` và `<script>` không còn hiệu lực | — |
| T4 | CC theo cấu hình (tác giả, codeowners, danh sách) và mức độ tối thiểu | Test từng chế độ | P09 T4 |
| T5 | `ScmPort.upsert_check` và chú thích theo dòng, kết luận luôn `neutral` | Test với GitHub giả | T1 |

## Cổng

```bash
make check
```

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** vai trò `author/reviewer/other` ở `Reply`, `Reaction`, `FeedbackEvent` và `resolve_states(trusted_roles)`; `sanitize.clean` vô hiệu @mention, #n, liên kết tự động, HTML, cắt độ dài, áp dụng cho mọi chuỗi do mô hình hoặc mã PR sinh ra; `compute_cc` (author, codeowners, list) chỉ khi có cảnh báo mở từ mức tối thiểu, kiểm tra handle, loại tài khoản bot, tối đa 10; `build_check` và `ScmPort.upsert_check` (check run luôn neutral, chú thích theo dòng, chia 50 một lượt); `GitHubApi` (get_pr, merge_base, get_file) và `GitHubScm` thử lại có lùi khi giới hạn tốc độ.
- **Khác kế hoạch:** thêm `GitHubApi` và `PrInfo` cho P11 ngay trong bộ chuyển đổi GitHub.
