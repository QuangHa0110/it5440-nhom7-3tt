# CLAUDE.md — IT5440 Nhóm 7, đề tài 3TT

Ngữ cảnh bền vững của repo. Đọc đầu mỗi phiên. Giữ file này dưới 150 dòng: nó là mục lục, không phải bách khoa.

## Dự án là gì

Nghiên cứu trường hợp: bot trong CI của công ty Z quét pull request, dùng LLM lọc cảnh báo của công cụ phân tích tĩnh,
rồi đăng một comment. So sánh 3 cách: A (chỉ công cụ quét), B (LLM + vài dòng mã), C (LLM + ngữ cảnh luồng dữ liệu).
Nguồn sự thật: [docs/proposal-llm-loc-canh-bao-pr.md](docs/proposal-llm-loc-canh-bao-pr.md). Tóm tắt môn học:
[docs/huong-dan-tieu-luan.md](docs/huong-dan-tieu-luan.md). Ngôn ngữ tài liệu và commit: tiếng Việt, mã và tên biến: tiếng Anh.

## Quy tắc cứng (repo PUBLIC)

- Không commit: tên công ty Z, tên dự án nội bộ, đoạn mã nguồn của Z, đường dẫn nội bộ, kết quả quét thô, secret, PDF bài báo.
- Dữ liệu thô nằm ở `results/raw/` hoặc `results/company/` (đã trong `.gitignore`). Chỉ số liệu tổng hợp ẩn danh, đã được Z duyệt, vào `results/`.
- Không dùng AI để tạo nhãn đáp án (proposal mục 10). Mọi số liệu và trích dẫn phải đối chiếu bản gốc.
- Cấu hình chạy `eval` phải được khóa bằng tag Git trước khi chạy (xem [docs/git-workflow.md](docs/git-workflow.md)).

## Nhánh và release (chi tiết: [docs/git-workflow.md](docs/git-workflow.md))

| Nhánh | Vai trò |
|---|---|
| `main` | Release candidate. Chỉ nhận merge từ `dev`. Release bằng tag `vX.Y.Z` do `bump-my-version` tạo |
| `dev` | Nhánh phát triển chung của cả nhóm. Nhận PR từ nhánh cá nhân |
| `{tên dev}/{slug}/{nội dung ngắn gọn}` | Nhánh cá nhân, ví dụ `trinq/context/taint-extractor`. Tách từ `dev`, PR về `dev` |

- Không push thẳng `main` hoặc `dev`. Không `--no-verify`, không force-push nhánh được bảo vệ (hook `.claude/hooks/guard-git-safety.py` chặn).
- Commit theo Conventional Commits: `feat|fix|docs|refactor|test|chore(scope): mô tả`. Một thay đổi logic cho mỗi commit.
- Phiên bản chỉ đổi bằng `make bump PART=patch|minor|major`, không sửa tay.

## Bản đồ thư mục

```
docs/        tài liệu: proposal, ADR, kế hoạch, devlog (xem docs/CLAUDE.md)
pipeline/    quét, chuẩn hóa, khử trùng lặp, file CI
rules/       luật Semgrep/CodeQL tùy biến
analysis/    hợp nhất, gán nhãn, thống kê
results/     chỉ số liệu ẩn danh đã duyệt
paper/       bài báo LaTeX và báo cáo
slides/      slide các lần báo cáo
```

## Lệnh thường dùng

`make help` liệt kê tất cả. Chính: `make setup`, `make lint`, `make test`, `make check` (cổng trước khi mở PR), `make bump`.

## Tài liệu như mã (docs-as-code)

Quyết định, kế hoạch hay ràng buộc không nằm trong repo thì coi như không tồn tại. Chọn đúng nơi:

- Quyết định đáng tranh luận → ADR trong `docs/adr/`.
- Việc nhiều bước (từ 3 task) → kế hoạch trong `docs/plans/`.
- Điều bất ngờ gặp khi làm → `docs/devlog/`.
- Nợ còn tồn → `docs/devlog/debt-ledger.md`.

Quy tắc thư mục `docs/` xem [docs/CLAUDE.md](docs/CLAUDE.md).

## Khi làm việc với Claude

- Đọc trước khi sửa. Thay đổi nhỏ nhất đạt mục tiêu, không refactor ngoài yêu cầu.
- Với việc ≥3 task: viết kế hoạch vào `docs/plans/queued/` trước khi code.
- Chỉ chạy test của phần vừa sửa khi đang làm. Chạy toàn bộ bằng `make check` một lần khi tích hợp.
- Không commit, không push, không mở PR nếu người dùng chưa yêu cầu.
