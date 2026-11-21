# Kịch bản 02 — PR nháp và thay đổi sạch

| Trường | Nội dung |
|---|---|
| Mục tiêu | Xác minh PR nháp không bị phân tích sớm; khi chuyển sang ready, PR không có lỗi bảo mật mới được xử lý bình thường. |
| Repo/PR | [`task-manager-project` — PR #2](https://github.com/vudinhminh08/task-manager-project/pull/2) |
| Tiền điều kiện | GitHub App nhận được `pull_request` và trạng thái draft/ready-for-review. |
| Kết quả mong đợi | Sự kiện mở PR nháp bị bỏ qua; sự kiện chuyển sang ready tạo lượt phân tích và kết quả không có cảnh báo mới. |

## Thực hiện và kết quả

PR được mở ở trạng thái draft với thay đổi tài liệu sạch. Không có job triage được tạo lúc mở PR. Sau khi chuyển PR sang ready for review, bot chạy và đăng “không có cảnh báo mới”; check `PR Triage` hoàn tất trạng thái `neutral`.

**Kết luận:** Đạt cho cả nhánh lọc draft và trường hợp không có phát hiện.

**Dọn dẹp:** PR đã đóng, không merge; nhánh thử đã xóa.
