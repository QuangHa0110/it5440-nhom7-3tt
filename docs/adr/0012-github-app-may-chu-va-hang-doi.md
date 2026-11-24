# ADR 0012 — Đóng gói thành GitHub App: máy chủ webhook, token cài đặt, hàng đợi bền, cấu hình đọc từ nhánh đích

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq (giao việc ngày 2026-11-13)
- **Liên quan:** [ADR 0007](0007-ba-job-tach-quyen.md), [ADR 0004](0004-cong-va-bo-chuyen-doi.md), [architecture.md](../architecture.md) mục 6

## Bối cảnh

Lõi xử lý đã chạy được như chương trình dòng lệnh, nhưng chưa có gì tự kích hoạt khi có PR. Người dùng muốn một sản phẩm thử được ngay trên GitHub. Một GitHub App có lợi thế so với GitHub Actions: comment đến từ danh tính của App kể cả khi PR đến từ fork, quyền được cấp theo từng repo, và token ghi không bao giờ nằm trong môi trường chạy mã của PR.

## Quyết định

- **D1.** Máy chủ FastAPI nhận webhook tại `POST /webhook`. Xác thực chữ ký `X-Hub-Signature-256` bằng so sánh thời gian hằng, từ chối thân quá 5 MB.
- **D2.** App xác thực bằng JWT RS256 (khóa riêng của App) để lấy token cài đặt cho từng installation, lưu đệm đến khi gần hết hạn. Token không bao giờ vào log, tham số dòng lệnh hay URL.
- **D3.** Mã của PR được lấy bằng `git fetch` theo SHA với tiêu đề xác thực truyền qua biến môi trường `GIT_CONFIG_*`. Bản đối chiếu là **merge-base** do API compare trả về, không phải đỉnh nhánh đích.
- **D4.** Hàng đợi bền trong SQLite (bảng `jobs`), thực thi bằng nhóm luồng. Mỗi lần giao (`X-GitHub-Delivery`) chỉ xử lý một lần, mỗi `(repo, pr, head_sha)` chỉ chạy một lần. Khi khởi động lại, việc đang dở được xếp lại hàng. Lượt chạy cũ hơn bị lượt mới thay thế thì không đăng kết quả.
- **D5.** **Cấu hình `.pr-triage.yml` chỉ đọc từ nhánh đích**, không đọc từ nhánh của PR, để người gửi PR không tự tắt bot hoặc nới ngưỡng.
- **D6.** Kết quả hiển thị bằng hai cách: một comment tổng hợp (cập nhật tại chỗ) và một check run có kết luận luôn là `neutral`, kèm chú thích theo dòng. Bot không bao giờ chặn merge.
- **D7.** Bỏ qua sự kiện do chính bot hoặc tài khoản bot khác gây ra, để không tạo vòng lặp.
- **D8.** Toàn bộ phần tương tác với GitHub nằm sau các cổng đã có (`ScmPort`) và một cổng mới `RepoFetcher`, nên test chạy bằng máy chủ GitHub giả và kho git cục bộ.

## Phương án khác

- **GitHub Actions:** không cần máy chủ, nhưng PR từ fork không có secret và không ghi được, và token ghi nằm cạnh mã của PR.
- **Webhook thẳng vào CLI qua CI bên ngoài:** thêm một tầng mà không thêm giá trị.
- **Hàng đợi ngoài (Redis, SQS):** phù hợp khi nhiều bản sao máy chủ. Một bản sao với SQLite đủ cho thử nghiệm và thí điểm.

## Hệ quả

- **Tốt hơn:** cài lên repo là chạy, không sửa workflow của khách, hoạt động với fork.
- **Tệ hơn:** phải vận hành một máy chủ có địa chỉ công khai và giữ khóa riêng của App.
- **Từ nay phải đúng:** khóa riêng, secret webhook và khóa LLM chỉ ở biến môi trường hoặc kho bí mật. Một bản sao máy chủ cho mỗi kho dữ liệu SQLite.
