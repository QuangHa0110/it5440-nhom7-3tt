# Kết quả E2E trên Gitea, GitLab CE và Jenkins

Bản nguồn được kiểm tra là commit `80dee82c7c4052048c319bcee9d7033be174f93b` của PR #10. Các bản sửa phát hiện trong lần chạy được đưa vào PR #10 cùng hồ sơ này.

## Môi trường

- Gitea 1.27.3 và GitLab CE 18.9.2 chạy trong Docker với repo demo riêng.
- Jenkins 2.580.2 chạy image từ `deploy/jenkins/Dockerfile`. Job poll dùng repo Gitea khác với repo thử webhook.
- LLM chạy tại chỗ bằng Ollama 0.17.0 và `qwen2.5-coder:3b`. Chỉ dùng mã demo của dự án.
- Semgrep 1.185.0 và bộ `p/default` 1.074 luật, SHA-256 `9c76333af7c9555a45560d8398cf5fa03432d8f86ca4e458eac3686599fd8f1b`.
- Fetch dự phòng được kiểm bằng cách cho lần fetch đầu PR qua SHA thất bại có kiểm soát rồi để GitFetcher lấy ref thật từ máy chủ. Commit nhận được khớp SHA gốc. Gitea dùng `refs/pull/1/head`, GitLab dùng `refs/merge-requests/1/head`.
- Khởi động GitLab đã nhận lại năm delivery bằng cơ chế resend của GitLab. MR cuối được đóng rồi mở lại để phát sinh webhook thật. Giới hạn 120 giây ở client LLM gây timeout khi nhiều luồng dùng chung một phiên inference. GitLab tiếp tục hàng đợi SQLite với Ollama riêng và giảm số tác vụ đồng thời.

## Thay đổi cần đưa vào bản phát hành

1. **Sửa Gitea xử lý JSON `null`.** Gitea trả `null` khi comment chưa có reaction. Phiên bản gốc sinh `TypeError` trong phân trang và bỏ lỡ phản hồi. Bản sửa coi `null` là kết thúc phân trang. Test hồi quy tái hiện lỗi trước khi sửa và qua sau khi sửa. Gitea thật ghi nhận `fp`, `tp`, `close`, `merge` sau khi khởi động lại bot với bản sửa.
2. **Cài Semgrep trong image bot.** Dockerfile gốc dùng `uv sync --no-dev` trong khi Semgrep nằm ở nhóm dev. Bản sửa dùng đúng phiên bản 1.185.0 như image Jenkins. GitLab E2E chạy trong image bổ sung Semgrep.
3. **Cập nhật lock của `p/default`.** Registry hiện trả SHA-256 khác lock gốc `760fa4379205c00f41b56a8b803ed9459ffaed91afe2e6f54c696b416dab72b1`. Lệnh `--frozen` báo lỗi với lock gốc và chạy được với lock cập nhật. Bản patch chỉ chứa lock, không kèm nội dung bộ luật.

## Jenkins

- Job poll #1 phát hiện PR mới. Job triage #1 fetch và đăng comment. Kết quả scan `degraded` vì hai verdict LLM timeout trong lượt chạy đồng thời.
- Sau khi đẩy commit mới, job poll #6 phát hiện thay đổi và tự gọi triage #2. Job fetch đúng đầu PR, chạy Semgrep, có bốn verdict B/C từ model thật và cập nhật đúng comment cũ. Build `SUCCESS`, trạng thái kết quả `ok`, không có lỗi verdict.

## Kết quả theo kịch bản

Cả Gitea và GitLab có 6/6 lượt quét demo ở trạng thái `ok`. Mỗi host có 16 verdict B/C từ model thật, không lỗi trong kết quả cuối. Mỗi PR/MR có đúng một comment của bot.

| Ca | Kết quả trên cả hai host |
| --- | --- |
| 01 SQL injection | Có CWE-89 và CWE-79. Phản hồi của reviewer cập nhật hai cảnh báo sang `marked_false` và `responded`. Đóng PR/MR được ghi vào SQLite. |
| 02 Truy vấn có tham số | Chỉ có CWE-79. |
| 03 Chú thích cố lừa bot | Có CWE-89 và CWE-79. Comment không chứa `@everyone`. |
| 04 Secret viết cứng | Có CWE-798. Comment đã che giá trị mẫu. |
| 05 Thay đổi vô hại | Comment báo không có cảnh báo mới. Push commit mới giữ nguyên ID comment. Merge được ghi vào SQLite. |
| 06 Ép kiểu số nguyên | Semgrep báo CWE-89. Model vẫn gán `likely_true` và cảnh báo vẫn mở rộng. Ca này chưa đạt kỳ vọng lọc cảnh báo sai. |

GitLab MR !1 từng vượt thời gian chờ của script theo dõi trong lần đổi cấu hình inference. SQLite và REST xác nhận lượt quét cuối sau khi app phục hồi hàng đợi đạt `ok` và đăng đúng một comment.

## Kiểm tra bản sửa

- `make check` qua Ruff, mypy và 427 test. Một test live mặc định được bỏ qua vì lệnh chạy bộ test không nhận biến cấu hình LLM. Ba luồng E2E ở trên gọi LLM thực tế.
- Image từ Dockerfile đã sửa build thành công. Chạy `semgrep --version` ngay trong image trả 1.185.0.
- Đề xuất `v0.1.0` sau khi đưa patch vào `dev`, xác minh `p/default` khớp lock, rồi merge `dev` → `main` với CI xanh. Ghi ca 06 và trạng thái chưa kiểm chứng máy chủ Bitbucket trong ghi chú phát hành.
