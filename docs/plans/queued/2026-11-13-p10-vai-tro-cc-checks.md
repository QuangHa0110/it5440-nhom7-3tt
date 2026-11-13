# P10. Vai trò phản hồi, CC, check run, làm sạch nội dung

- **Status:** queued
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0014, ADR 0012 D6
- **Nhánh:** `trinq/bot/roles-cc-checks`
- **Bắt đầu / Kết thúc:** — / —

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
