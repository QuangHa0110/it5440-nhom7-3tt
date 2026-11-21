# Kết quả end-to-end — 2026-11-17

## Tổng hợp

| PR | Trường hợp | Kết quả bot | Feedback | Trạng thái |
|---|---|---|---|---|
| [#1](https://github.com/vudinhminh08/task-manager-project/pull/1) | SQL injection trong fixture | Một cảnh báo High/CWE-89, check `PR Triage` hoàn tất `neutral` | `tp` được nhận và lưu | Đạt |
| [#2](https://github.com/vudinhminh08/task-manager-project/pull/2) | Draft rồi ready; thay đổi tài liệu sạch | Draft bị bỏ qua; sau khi ready báo không có cảnh báo mới | Không áp dụng | Đạt |
| [#3](https://github.com/vudinhminh08/task-manager-project/pull/3) | SQL nối chuỗi với tên cột đã allowlist | Scanner phát hiện pattern; LLM đưa vào nhóm có thể báo sai | `fp` được nhận và lưu | Đạt |

Ba lượt triage có trạng thái run `ok`. PR thử nghiệm đều đóng, không merge; các nhánh thử đã xóa.

## Phạm vi và giới hạn

- Đây là kiểm thử tích hợp trên ba fixture/PR có chủ đích, không phải đánh giá độ chính xác trên tập dữ liệu đại diện hoặc nhiều repo.
- PR #2 chỉ xác nhận trường hợp thay đổi sạch cụ thể; nó không chứng minh không có false negative nói chung.
- PR #3 xác nhận hành vi trên allowlist hẹp gồm hai tên cột; cần thêm biến thể để kết luận rộng hơn.
- Bot đăng comment và check nhưng không chặn merge.
- Không lưu SARIF thô, API key hay secret webhook trong hồ sơ này.
