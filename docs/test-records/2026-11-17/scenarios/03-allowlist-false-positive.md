# Kịch bản 03 — SQL nối chuỗi an toàn nhờ allowlist

| Trường | Nội dung |
|---|---|
| Mục tiêu | Kiểm tra LLM dùng ngữ cảnh mã để phân loại một pattern mà scanner có thể báo nhầm. |
| Repo/PR | [`task-manager-project` — PR #3](https://github.com/vudinhminh08/task-manager-project/pull/3) |
| Tiền điều kiện | Fixture Java lấy tên cột sort từ request nhưng chỉ chấp nhận `title` hoặc `created_at` trước khi dựng SQL. |
| Kết quả mong đợi | Scanner có thể phát hiện phép nối; bộ lọc nhận ra allowlist giới hạn đầu vào và xếp cảnh báo vào nhóm có thể báo sai. |

## Thực hiện và kết quả

Semgrep phát hiện pattern nối chuỗi vào câu SQL. Bot báo “0 cảnh báo cần xem” và đưa một cảnh báo vào phần có thể là báo sai; phần giải thích ghi nhận `sortColumn` chỉ nhận giá trị từ allowlist hoặc giá trị mặc định. Người thực hiện gửi `fp` theo mã cảnh báo; feedback được lưu và xử lý.

**Kết luận:** Đạt cho fixture an toàn cụ thể này. Kết quả không chứng minh bộ lọc phân loại đúng mọi dạng allowlist.

**Dọn dẹp:** PR đã đóng, không merge; nhánh thử đã xóa.
