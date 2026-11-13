# Cài đặt và vận hành GitHub App

Thiết kế: [ADR 0012](adr/0012-github-app-may-chu-va-hang-doi.md). Bot nhận webhook của GitHub, quét phần mã thay đổi của PR, để LLM lọc cảnh báo, rồi đăng **một comment** (cập nhật tại chỗ) và **một check run** có kết luận `neutral` kèm chú thích theo dòng. Bot không chặn merge và không sửa mã.

## Thử trên máy của bạn (khoảng 15 phút)

Cần: Docker (hoặc Python 3.12 và `uv`), `git`, một repo GitHub thử, khóa LLM, và `npx` (Node) để chuyển tiếp webhook.

**1. Cấu hình.**

```bash
cp .env.example .env
openssl rand -hex 16        # dán vào PR_TRIAGE_ALIAS_SALT
openssl rand -hex 16        # dán vào PR_TRIAGE_ADMIN_TOKEN
```

Điền `PR_TRIAGE_LLM_API_KEY`, `PR_TRIAGE_LLM_MODEL`. Chỉ đặt `PR_TRIAGE_LLM_ALLOW_EXTERNAL=1` khi repo thử là mã nguồn mở hoặc mã giả. Nên đặt `PR_TRIAGE_ALLOWED_REPOS=OWNER/NAME` để App chỉ làm việc trên repo thử.

**2. Mở đường cho webhook.** Vào https://smee.io/new để lấy một địa chỉ, rồi chạy:

```bash
npx smee-client --url https://smee.io/XXXX --target http://localhost:8080/webhook
```

**3. Tạo GitHub App từ manifest.**

```bash
python scripts/github_app_manifest.py html --webhook-url https://smee.io/XXXX --name "PR Triage của TÊN BẠN"
```

Mở `app-manifest.html` trong trình duyệt đã đăng nhập GitHub, bấm nút và xác nhận. GitHub chuyển về `http://localhost:3000/?code=...` (trang trống là bình thường). Chép giá trị `code` rồi chạy:

```bash
python scripts/github_app_manifest.py exchange CODE --out secrets/
```

Lệnh này ghi `secrets/<tên>.env` (ID, đường dẫn khóa riêng, secret webhook) và tệp `.pem` với quyền `0600`, không in bí mật ra màn hình. Chép ba giá trị đó vào `.env`. **Không commit thư mục `secrets/`.**

**4. Chạy máy chủ.**

```bash
docker compose up --build        # hoặc: uv run pr-triage serve --port 8080
curl http://localhost:8080/healthz
```

**5. Cài App lên repo thử.** Trên trang của App chọn *Install App*, chọn đúng repo. Mở một PR (xem [demo.md](demo.md)) và đợi khoảng 15 đến 60 giây: comment và check **PR Triage** xuất hiện.

## Cấu hình theo repo: `.pr-triage.yml`

Đặt ở gốc repo. **Bot chỉ đọc tệp này từ nhánh đích** (nhánh `main`), nên người gửi PR không tự tắt được bot hay nới ngưỡng. Khóa lạ hoặc giá trị sai bị từ chối và bot báo ngay trong PR.

```yaml
version: 1
enabled: true
mode: comment            # comment | shadow (shadow: chạy và lưu kết quả nhưng không đăng gì)
display: C               # A | B | C: cách LLM nào được đăng
paths:
  include: []            # rỗng là mọi tệp
  exclude: ["**/target/**", "**/test/**"]
severity:
  min_comment: low       # low | medium | high | critical
secrets:
  enabled: true
mentions:
  mode: [author, codeowners, list]   # none | author | codeowners | list
  users: ["@sec-team"]               # bắt buộc khi có list
  min_severity: high                 # chỉ CC khi có cảnh báo từ mức này
feedback:
  trusted_roles: [reviewer]          # phản hồi `fp` của vai trò nào làm cảnh báo thành "bị đánh dấu sai"
check_run:
  enabled: true
limits:
  max_changed_files: 300
  max_findings: 40
```

Với PR từ bên ngoài (outsource), nên đặt `feedback.trusted_roles: [reviewer]` để phản hồi `fp` của chính tác giả không có hiệu lực ([ADR 0014](adr/0014-phan-hoi-theo-vai-tro-va-cc.md)). CC (`@mention`) chỉ gồm tác giả PR, người trong `CODEOWNERS` của nhánh đích hoặc danh sách cấu hình, không bao giờ lấy từ nội dung do mô hình sinh. Chỉnh sửa comment không gửi lại thông báo cho người mới được thêm vào CC.

## Lập trình viên dùng bot thế nào

- Đọc comment. Mỗi cảnh báo có một mã ngắn, ví dụ `59d4c2`.
- Cảnh báo sai: trả lời một comment mới với `fp 59d4c2 lý do ngắn`. Cảnh báo đúng: `tp 59d4c2`.
- Cảnh báo bị thu gọn (`<details>`) là những cái LLM cho là có thể báo sai. Vẫn mở ra xem được.
- Đẩy commit sửa lỗi: lượt chạy sau tự ghi nhận cảnh báo đã được sửa.
- Bot không bao giờ nói thay đổi là "an toàn". "Không có cảnh báo" chỉ nghĩa là công cụ quét không thấy gì.

## Quyền của App

| Quyền | Lý do |
|---|---|
| Contents: read | Lấy mã của PR, đọc `.pr-triage.yml` và `CODEOWNERS` ở nhánh đích |
| Pull requests: write | Đăng và cập nhật comment, đọc câu trả lời và phản ứng |
| Checks: write | Tạo check run kèm chú thích |
| Metadata: read | Bắt buộc của GitHub |

Sự kiện đăng ký: `pull_request`, `issue_comment`. App không xin quyền ghi mã, quản trị hay secrets.

## Bảo mật

- **Mã của PR không bao giờ được chạy.** Bot chỉ đọc văn bản: Semgrep và tree-sitter phân tích tĩnh, LLM không có công cụ.
- **PR từ fork** hoạt động bình thường: comment đến từ danh tính của App, token ghi nằm trong máy chủ chứ không trong môi trường chạy mã của PR.
- **Token** cài đặt được lưu đệm trong bộ nhớ, truyền cho `git fetch` qua biến môi trường (`GIT_CONFIG_*`), không vào tham số dòng lệnh, URL hay log.
- **Webhook** bị từ chối nếu chữ ký `X-Hub-Signature-256` sai hoặc thiếu, hoặc thân lớn hơn 5 MB. Mỗi lần giao (`X-GitHub-Delivery`) chỉ xử lý một lần.
- **Nội dung do mô hình sinh** được làm sạch trước khi vào comment: `@mention`, `#số`, liên kết và HTML bị vô hiệu.
- **Secret trong mã** bị che từ lúc phát hiện, kể cả trong kho dữ liệu và trong prompt gửi LLM.
- **Giới hạn phạm vi:** đặt `PR_TRIAGE_ALLOWED_REPOS` để chỉ xử lý repo mong muốn. Người cài App lên repo khác sẽ không kích hoạt được chi phí LLM.
- **Dừng khẩn cấp:** gỡ cài đặt App, hoặc đặt `enabled: false` ở nhánh đích, hoặc dừng container.

## Vận hành

| Việc | Cách làm |
|---|---|
| Sức khỏe | `GET /healthz` (sống), `GET /readyz` (kho dữ liệu dùng được) |
| Thống kê | `GET /stats` và `GET /metrics` với tiêu đề `X-Admin-Token`. Không đặt `PR_TRIAGE_ADMIN_TOKEN` thì hai endpoint này bị ẩn (404) |
| Dữ liệu | SQLite ở `data/app/store.sqlite` (volume `/data` trong Docker). Sao lưu bằng cách sao chép khi dừng máy chủ, hoặc `sqlite3 store.sqlite ".backup out.sqlite"` |
| Khởi động lại | Việc đang dở được xếp lại hàng và chạy tiếp |
| Xoay khóa | Tạo khóa riêng mới trên trang App, cập nhật `GITHUB_APP_PRIVATE_KEY_PATH`, khởi động lại |
| Đổi muối bí danh | Không đổi sau khi đã thu dữ liệu (người thao tác được băm với muối này) |
| Số việc song song | `PR_TRIAGE_WORKERS` (số PR cùng lúc), `PR_TRIAGE_PIPELINE_WORKERS` (cuộc gọi LLM song song trong một PR) |

## Xử lý sự cố

| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| Không có gì xảy ra khi mở PR | Webhook chưa tới (xem Recent Deliveries trên trang App), smee chưa chạy, repo không nằm trong `PR_TRIAGE_ALLOWED_REPOS`, PR đang là bản nháp |
| 401 ở webhook | Secret webhook trong `.env` khác secret của App |
| Comment "cấu hình `.pr-triage.yml` sai" | Sửa tệp ở nhánh đích theo danh sách lỗi trong comment |
| Comment "chưa quét xong" | Lỗi khi lấy mã hoặc quét. Xem `GET /stats`, trường `error` của việc gần nhất |
| Comment chỉ có "không có cảnh báo mới" dù có lỗ hổng | Luật quét không phủ loại lỗi đó (hiện luật tùy chỉnh phủ SQL injection, cùng bộ quét secret) |
| Không đăng được check run | App thiếu quyền Checks: write. Cấp quyền rồi chấp nhận trên trang cài đặt |

## Giới hạn hiện tại

- Chỉ GitHub (GitLab và Bitbucket cần thêm một bộ chuyển đổi cho `ScmPort`).
- Phân tích ngữ cảnh luồng dữ liệu chỉ cho Java. Quét secret chạy với mọi ngôn ngữ.
- Một bản sao máy chủ cho mỗi kho SQLite.
- Chưa có giao diện quản trị. Chưa có comment theo dòng kiểu review, thay bằng chú thích của check run.
