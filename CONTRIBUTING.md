# Đóng góp

Quy trình đầy đủ: [docs/git-workflow.md](docs/git-workflow.md). Tóm tắt:

1. `git switch dev && git pull`, rồi `git switch -c {tên dev}/{slug}/{nội dung}`.
2. Commit nhỏ theo Conventional Commits (`type(scope): mô tả`).
3. `make check` phải qua trước khi mở PR vào `dev`.
4. Không commit tên công ty Z, mã nguồn, đường dẫn nội bộ, kết quả quét thô hay secret. Repo này public.

Mỗi thư mục con của `src/pr_triage/` có người phụ trách trong `.github/CODEOWNERS`.
