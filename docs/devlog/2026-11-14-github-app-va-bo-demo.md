# Tóm tắt đợt GitHub App (P08 đến P12)

- **Ngày:** 2026-11-13 đến 2026-11-14. Người dùng giao: "dev hết các tính năng cho sản phẩm hoàn thiện cơ bản, đưa thành GitHub App để thử luôn". ADR 0012 đến 0014, kế hoạch P08 đến P12.

## Đã xong

Quét secret (che giá trị từ lúc phát hiện), cấu hình `.pr-triage.yml` đọc từ nhánh đích, bộ lọc đường dẫn, ngưỡng mức độ, giới hạn số cảnh báo, CODEOWNERS, vai trò phản hồi (`author`, `reviewer`, `other`), CC theo chính sách, làm sạch nội dung do mô hình sinh, check run `neutral` có chú thích theo dòng, máy chủ GitHub App (webhook có chữ ký, JWT, token cài đặt, `git fetch` theo SHA, hàng đợi bền idempotent, thay thế lượt cũ, phát hiện đã sửa), Docker, manifest tạo App, bộ demo sáu PR. `make check`: 237 test qua.

Đã kiểm chứng: toàn bộ luồng App chạy với **GitHub giả**, kho git cục bộ, Semgrep thật và **LLM thật** (comment tiếng Việt, check run neutral, CC tác giả). Container Docker chạy được (không root, `/healthz`, chữ ký sai bị từ chối).

## Chưa kiểm chứng

- **Chưa gọi GitHub thật lần nào.** Chưa nhận webhook thật, chưa tạo App thật. Cần người dùng đăng ký App theo `docs/github-app.md` rồi thử.
- Hình dạng phản hồi thật của GitHub có thể khác bản giả ở các chi tiết (ví dụ phân trang, mã lỗi, tên trường `author_association`).
- Chưa thử với repo lớn, monorepo, hay nhiều PR đồng thời. `SymbolIndex.calls_of` quét lại toàn repo mỗi truy vấn.
- Chưa thử PR từ fork thật (đã thử dự phòng `refs/pull/N/head` ở mức kho cục bộ).
- Luật quét tùy chỉnh chỉ phủ SQL injection. Cảnh báo "không có cảnh báo mới" không có nghĩa là an toàn.

## Phát hiện trong lúc làm

- Luật nối chuỗi ban đầu bỏ sót mẫu "dựng chuỗi SQL ở biến rồi mới `executeQuery(biến)`" (phổ biến nhất). Đã thêm `java-sql-concat-flow`. Semgrep CE vẫn không nối taint xuyên hàm (xem devlog 2026-11-13).
- Kiểm thử đồng thời lộ ra SQLite dùng chung giữa các luồng cần khóa (đã sửa ở P06).

## Quyết định tự đưa ra

- Cấu hình repo đọc từ **nhánh đích**, không từ nhánh của PR.
- Check run luôn `neutral`; chú thích dùng mức `warning` cho `high` trở lên, `notice` cho còn lại.
- Hàng đợi là SQLite trong tiến trình (một bản sao máy chủ). Đổi sang hàng đợi ngoài khi cần nhiều bản sao.
- Danh sách repo cho phép là biến môi trường (`PR_TRIAGE_ALLOWED_REPOS`), mặc định cho mọi repo đã cài.
