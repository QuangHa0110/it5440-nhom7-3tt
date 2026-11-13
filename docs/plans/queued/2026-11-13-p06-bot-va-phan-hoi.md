# P06. Bot comment và thu phản hồi

- **Status:** queued
- **Người làm:** trinq (với Claude Code)
- **Đóng:** comment một lần cập nhật tại chỗ, thu phản hồi theo từng cảnh báo
- **Quyết định cho phép:** ADR 0007, 0010
- **Nhánh:** `trinq/bot/comment-and-feedback`
- **Bắt đầu / Kết thúc:** — / —

---

## Bối cảnh

SCM của Z chưa biết. Bộ chuyển đổi đầu tiên là **GitHub** vì nhóm kiểm thử được trên repo của mình. Một bộ **giả** trong bộ nhớ dùng cho test và cho `make e2e`.

## Ngoài phạm vi

GitLab và Bitbucket. Comment theo dòng cho mức High (ADR 0010 D4). Gửi bất cứ thứ gì lên repo thật của nhóm khi chưa có lệnh của người dùng.

## Hiện trạng đã kiểm chứng

Chưa viết gì.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `CommentRenderer`: một comment, khối `<details>` cho `likely_false`, mã ngắn cho mỗi cảnh báo, cú pháp `fp`/`tp` ở đầu | Test so khớp với mẫu dự kiến (snapshot), không chứa mã quá 5 dòng mỗi cảnh báo | P05 T4 |
| T2 | `FakeScm` và bộ test hợp đồng cho `ScmPort` | Cùng bộ test chạy được trên bộ giả; sẵn sàng cho bộ thật | P01 |
| T3 | `Publisher`: tìm comment cũ theo dấu ẩn, cập nhật tại chỗ, chế độ `shadow` không gọi SCM | Test: chạy hai lần chỉ có một comment | T1, T2 |
| T4 | `GitHubScm` bằng API REST, token từ biến môi trường | Test hợp đồng trên máy chủ giả HTTP; chưa gọi GitHub thật | T2 |
| T5 | `FeedbackCollector`: đọc trả lời `fp`/`tp`, phản ứng, commit, trạng thái PR, ẩn danh người thao tác | Test: các chuyển trạng thái của sơ đồ 8 | T2 |
| T6 | Phát hiện "đã sửa" (dấu vân tay biến mất và hàm có trong diff) | Test: file bị xóa không tính là đã sửa | T5, P02 |
| T7 | Lệnh `publish` và `feedback` | Chạy với `FakeScm` trong `make e2e` | T3, T5 |

## Cổng

```bash
make check
```

Gọi GitHub thật chỉ khi người dùng yêu cầu và chỉ trên một PR thử do người dùng chỉ định.

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Giới hạn tốc độ API | Lỗi 403 hoặc 429 | Thử lại có lùi, ghi vào log |
| Bot đăng nhầm lên repo thật | Chạy `publish` mà không có cờ rõ | `publish` mặc định `--dry-run`, chỉ đăng khi có `--post` |

---

## Kết quả

*Điền khi đóng.*
