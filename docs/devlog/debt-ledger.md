# Sổ nợ

Chỉ ghi **cái còn nợ**. Thêm một dòng ngay khi nợ phát sinh. Khi đóng, chuyển nội dung sang mục devlog đã đóng nó và để lại một dòng tham chiếu ở đây.

| Id | Nợ | Phát sinh | Chủ | Đóng bởi |
|---|---|---|---|---|
| TD-1 | Bật branch protection cho `main` và `dev` trên GitHub (cần quản trị viên repo) | 2026-11-13 | | |
| TD-2 | Chốt công cụ quét và ngôn ngữ chính khi Z trả lời Phụ lục A, rồi điền `[project]` dependencies và workflow CI tương ứng. *2026-11-19: công cụ quét đã chốt (ADR 0019); còn ngôn ngữ chính và dependencies* | 2026-11-13 | | |
| TD-5 | Đường Jenkins chưa tách quyền theo ADR 0007: một container giữ cả token ghi, khóa LLM và chạy mã PR | 2026-11-17 | | |
| TD-6 | Chưa chạy lại `deploy/jenkins/` trong Docker sau khi thay `ci_helper.py` bằng `pr-triage ci` (P14); chưa kiểm chứng LLM thật, comment thật, webhook thật | 2026-11-20 | | |
| TD-7 | Trên Windows, Semgrep trả đường dẫn dạng `src\app\X.java`: dấu vân tay và so khớp đường dẫn khác Linux, 4 test hỏng. `tests/app/fakegithub.py` ghi file không chỉ định `utf-8`. Chuẩn hóa đường dẫn về `/` trong `scan/sarif.py` (xem devlog 2026-11-19-p14) | 2026-11-19 | | |
| TD-8 | Bộ chuyển đổi GitLab, Gitea, Bitbucket Server chưa thử với máy chủ thật; Bitbucket Server chưa đối chiếu REST với tài liệu chính thức (chỉ webhook). Cần một lần chạy thật cho từng loại: webhook, comment tạo và cập nhật, lấy mã theo SHA và theo ref PR | 2026-11-22 | | |
