# `mask()` bỏ sót `_auth=` của `.npmrc` 🟡

- **Ngày:** 2026-11-25. Kế hoạch [P17](../plans/active/2026-11-25-p17-thu-du-lieu-oss-sonnh.md). Nợ: TD-9.

**Phát hiện.** Ở PR `mesh -190` (gentics/mesh), Semgrep báo 3 cảnh báo `detected-npm-registry-auth-token` trong
`js/.npmrc`, dạng `//<registry>/:_auth=<base64 của user:password>`. `triage-result.json` của lượt chạy chứa nguyên
giá trị này trong trường `snippet` (6 lần). Comment do `publish` in ra thì không có, vì comment chỉ gồm giải thích.
Thử `core/secrets.mask` bằng giá trị giả: `:_auth=dXNlcjpwYXNzd29yZA==` không bị che, `:_authToken=...` bị che
(mẫu `credential-assignment` chỉ khớp khi tên khóa chứa `token`, `secret`, `password`...).

**Vì sao quan trọng.** `mask` là lớp che secret trước khi đoạn mã vào cơ sở dữ liệu và prompt (`llm/redact.py`,
`context/bundle.py`). Với mã của Z, một `.npmrc` có `_auth=` sẽ đưa thông tin đăng nhập thật vào SQLite và có thể
tới LLM ngoài. Lần này giá trị vốn công khai trên repo gốc nên không phải rò rỉ mới.

**Đề xuất điều chỉnh.** Thêm mẫu cho `_auth\s*=` (và có thể `_password\s*=` của `.npmrc`) vào `PATTERNS`, kèm test.
Chưa sửa trong P17 vì ngoài phạm vi.
