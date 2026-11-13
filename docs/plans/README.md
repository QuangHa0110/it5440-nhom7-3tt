# `docs/plans/` — vòng đời kế hoạch

Kế hoạch là một đơn vị công việc có thể commit, với điều kiện hoàn thành quan sát được. Thư mục cho biết trạng thái, nên trả lời "đang làm gì" bằng `ls`.

| Bucket | Ý nghĩa | Ai chuyển, khi nào |
|---|---|---|
| `queued/` | Sẵn sàng chạy, có thứ tự. Chưa ai làm | Tác giả, khi viết xong |
| `active/` | Đang có người làm. Mỗi kế hoạch một người nhận | Người làm, khi bắt đầu |
| `done/` | Xong, điều kiện hoàn thành đã được kiểm chứng | Người làm, ở commit đóng |
| `failed/` | Bỏ dở hoặc bị thay thế, giữ lại kèm lý do | Người làm, khi dừng |

- Tên: `YYYY-MM-DD-<slug>.md` (hoặc thư mục cùng tên nếu có tài liệu kèm). Bắt đầu từ [_template.md](_template.md).
- Chuyển bucket bằng `git mv`, không sao chép.
- `done/` và `failed/` là hồ sơ lịch sử: chú thích bằng ghi chú có ngày, không viết lại phần thân.
- Công cụ Claude Code ghi kế hoạch mới vào `queued/` (xem `.claude/settings.json`), người làm chuyển tay sang `active/`.
- Cần kế hoạch khi việc có từ 3 task trở lên.

## Thứ tự trong `queued/`

Thứ tự chạy ghi ở đây khi khác thứ tự tên file. Hiện chưa có kế hoạch nào.
