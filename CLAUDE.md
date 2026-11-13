# CLAUDE.md — IT5440 Nhóm 7, đề tài 3TT

Ngữ cảnh bền vững của repo. Đọc đầu mỗi phiên. Giữ file này dưới 150 dòng: nó là mục lục, không phải bách khoa.

## Dự án là gì

Nghiên cứu trường hợp: bot trong CI của công ty Z quét pull request, dùng LLM lọc cảnh báo của công cụ phân tích tĩnh,
rồi đăng một comment. So sánh 3 cách: A (chỉ công cụ quét), B (LLM + vài dòng mã), C (LLM + ngữ cảnh luồng dữ liệu).
Nguồn sự thật: [docs/project/proposal-llm-loc-canh-bao-pr.md](docs/project/proposal-llm-loc-canh-bao-pr.md). Tóm tắt môn học:
[docs/project/huong-dan-tieu-luan.md](docs/project/huong-dan-tieu-luan.md). Ngôn ngữ tài liệu và commit: tiếng Việt, mã và tên biến: tiếng Anh.

## Quy tắc cứng (repo PUBLIC)

- Không commit: tên công ty Z, tên dự án nội bộ, đoạn mã nguồn của Z, đường dẫn nội bộ, kết quả quét thô, secret, PDF bài báo.
- Dữ liệu thô nằm ở `data/raw/` hoặc `data/company/` (đã trong `.gitignore`). Chỉ số liệu tổng hợp ẩn danh, đã được Z duyệt, vào `reports/results/`.
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
src/pr_triage/   package Python, mỗi thư mục con ứng với một phần việc
  core/ store/ pipeline/ scan/ normalize/ context/ llm/ bot/ evaluation/ app/   cli.py
tests/           phản chiếu src/, dữ liệu giả ở tests/fixtures/
deploy/ demo/    manifest GitHub App, ứng dụng mẫu và kịch bản demo
configs/         semgrep/ prompts/ schemas/ eval/ (cấu hình có phiên bản, khóa bằng tag)
data/            dữ liệu chạy, KHÔNG commit (chỉ README)
reports/         results/ (số liệu ẩn danh đã duyệt), paper/, slides/
docs/            project/ (proposal, tài liệu môn), adr/, plans/, devlog/
scripts/         script tiện ích của repo (không phải mã sản phẩm)
```

`app/` là GitHub App (máy chủ webhook, hàng đợi, xử lý sự kiện), xem docs/github-app.md.
Ranh giới mã: mọi gói phụ thuộc `core`, `core` không phụ thuộc gói nào; `context`, `llm`, `evaluation` không import `bot`; chỉ `pipeline` và `cli` nối các gói với nhau. Mỗi thư mục con trong `src/` có một người phụ trách (xem `.github/CODEOWNERS`).

## Lệnh thường dùng

`make help` liệt kê tất cả. Chính: `make setup`, `make lint`, `make typecheck`, `make test`, `make check` (cổng trước khi mở PR), `make e2e` (cần khóa LLM trong `.env`), `make bump`.
Khóa LLM chỉ ở biến môi trường hoặc `.env`, không bao giờ vào repo, log, devlog hay commit.

## Tài liệu như mã (docs-as-code)

Quyết định, kế hoạch hay ràng buộc không nằm trong repo thì coi như không tồn tại. Chọn đúng nơi:

| Bề mặt | Chứa | Không chứa |
|---|---|---|
| `docs/project/` | Proposal đã chốt (nguồn sự thật về phạm vi), tài liệu môn học, link bài báo | Tiến độ, nhật ký, PDF |
| `docs/adr/` | Mỗi file một quyết định đáng tranh luận: Bối cảnh / Quyết định / Phương án khác / Hệ quả | Cập nhật tiến độ |
| `docs/plans/` | Việc nhiều bước (từ 3 task), vòng đời `queued → active → done \| failed` | Quyết định (thuộc ADR) |
| `docs/devlog/` | Điều bất ngờ gặp khi làm, mỗi mục một file có ngày | Báo cáo "đã xong" (thuộc `plans/done/`) |
| `docs/devlog/debt-ledger.md` | Nợ còn tồn, chỉ nợ chưa đóng | Nợ đã đóng (chuyển vào devlog) |

- ADR chỉ thêm, không sửa; muốn đổi thì viết ADR mới thay thế và thêm con trỏ vào ADR cũ. Số thứ tự liên tục, kiểm tra `ls docs/adr | tail -1`.
- Kế hoạch xong được chú thích bằng ghi chú có ngày, không viết lại thân. Chuyển bucket bằng `git mv`. Mỗi task là một commit có điều kiện hoàn thành quan sát được.
- Khi đổi tên đường dẫn: cập nhật tài liệu sống, giữ nguyên `plans/done`, `plans/failed`, `devlog`; chú thích nếu để nguyên gây hiểu nhầm.
- Số liệu không bắt nguồn từ tài liệu viết tay: lấy từ `reports/results/`, tạo bằng script trong `src/pr_triage/evaluation/`.

## Khi làm việc với Claude

- Đọc trước khi sửa. Thay đổi nhỏ nhất đạt mục tiêu, không refactor ngoài yêu cầu.
- Với việc ≥3 task: viết kế hoạch vào `docs/plans/queued/` trước khi code.
- Chỉ chạy test của phần vừa sửa khi đang làm. Chạy toàn bộ bằng `make check` một lần khi tích hợp.
- Không commit, không push, không mở PR nếu người dùng chưa yêu cầu.
