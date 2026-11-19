# Kịch bản 01 — SQL injection thật

| Trường | Nội dung |
|---|---|
| Mục tiêu | Kiểm tra bot nhận diện và trình bày một lỗ hổng SQL injection có thể khai thác. |
| Repo/PR | [`task-manager-project` — PR #1](https://github.com/vudinhminh08/task-manager-project/pull/1) |
| Tiền điều kiện | GitHub App được cài vào repo; webhook và pipeline LLM hoạt động; PR chứa fixture Java cố ý dễ tổn thương. |
| Kết quả mong đợi | Bot đăng cảnh báo CWE-89 với vị trí mã; check `PR Triage` hoàn tất; phản hồi `tp` được nhận. |

## Thực hiện và kết quả

PR đưa dữ liệu từ tham số request vào câu SQL bằng nối chuỗi, không dùng tham số hóa. GitHub gửi sự kiện PR đến webhook; bot quét diff và đăng cảnh báo mức High tại dòng 18 của fixture. Check kết thúc trạng thái `neutral`, tiêu đề cho biết có một cảnh báo cần xem. Người thực hiện gửi `tp` cùng mã cảnh báo; sự kiện feedback được xử lý thành công.

**Kết luận:** Đạt. Mã fixture được xác nhận là true positive trong phạm vi kịch bản này.

**Dọn dẹp:** PR đã đóng, không merge; nhánh thử đã xóa.
