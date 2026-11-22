# Máy chủ git được hỗ trợ

Bot nói chuyện với bốn loại máy chủ qua một lớp nhà cung cấp (ADR 0021). Mã định danh repo:

| Máy chủ | Mã định danh | Ví dụ |
|---|---|---|
| GitHub | `owner/repo` (không tiền tố) | `acme/web` |
| GitLab | `gitlab:nhóm[/nhóm con]/dự-án` | `gitlab:acme/platform/api` |
| Gitea | `gitea:org/repo` | `gitea:acme/web` |
| Bitbucket Server / Data Center | `bitbucket:KHOA/repo` | `bitbucket:ACME/web` |

Mã định danh dùng nguyên trong `PR_TRIAGE_ALLOWED_REPOS` và `PR_TRIAGE_ROUTES` (mẫu kiểu shell, ví dụ `gitlab:acme/*`).

## Cấu hình

| Biến | Ý nghĩa |
|---|---|
| `PR_TRIAGE_<LOẠI>_URL` | Địa chỉ gốc của máy chủ. Đặt biến này là bật loại đó. `<LOẠI>` là `GITLAB`, `GITEA` hoặc `BITBUCKET` |
| `PR_TRIAGE_<LOẠI>_TOKEN` | Mã truy cập của tài khoản bot: đọc mã và comment trên PR |
| `PR_TRIAGE_<LOẠI>_WEBHOOK_SECRET` | Bí mật xác thực webhook |
| `PR_TRIAGE_<LOẠI>_BOT_LOGIN` | Tên tài khoản bot, để bỏ qua sự kiện do chính bot gây ra. GitLab và Gitea cũng dùng làm tên đăng nhập git |

GitHub App vẫn dùng các biến `GITHUB_APP_*`. Khi đã bật ít nhất một máy chủ khác, có thể bỏ trống toàn bộ `GITHUB_APP_*` và `GITHUB_WEBHOOK_SECRET`.

## Webhook

Trỏ webhook của máy chủ tới `https://<pr-triage>/webhook/<loại>` (`gitlab`, `gitea`, `bitbucket`); GitHub vẫn là `/webhook`.

| Máy chủ | Sự kiện cần bật | Xác thực |
|---|---|---|
| GitLab | Merge request events, Comments | Secret token (`X-Gitlab-Token`) |
| Gitea | Pull request, Issue comment | HMAC-SHA256 (`X-Gitea-Signature`) |
| Bitbucket Server | `pr:opened`, `pr:from_ref_updated`, `pr:modified`, `pr:merged`, `pr:declined`, `pr:deleted`, `pr:comment:added` | HMAC-SHA256 (`X-Hub-Signature: sha256=...`) |

Kênh định tuyến của các webhook này là `webhook` (`PR_TRIAGE_ROUTES=webhook:gitlab:acme/*,jenkins:gitlab:legacy/*`).

## Khác biệt so với GitHub

- **Không có check run.** Kết quả chỉ ở comment (ADR 0021 D5).
- **Phản ứng emoji:** GitLab và Gitea có; Bitbucket Server không có, phản hồi qua `fp <mã>` và `tp <mã>`.
- **Vai trò người phản hồi:** GitLab xét quyền thành viên (từ Developer trở lên là `reviewer`), Gitea xét cộng tác viên, Bitbucket xét danh sách người xem xét của PR.
- **Số tệp thay đổi:** Gitea (nếu thiếu) và Bitbucket không trả; giới hạn `max_changed_files` không kích hoạt ở đó.
- **Cấu hình `.pr-triage.yml` và CODEOWNERS** vẫn chỉ đọc từ nhánh đích.

## Jenkins

`pr-triage ci poll` và `pr-triage ci fetch` dùng cùng lớp này, nên job trung tâm quét được repo của mọi loại. Webhook Generic Webhook Trigger trong `casc.yaml` chỉ cấu hình sẵn cho GitHub; máy chủ khác dùng job poll hoặc webhook của máy chủ pr-triage. Token máy chủ ngoài GitHub đặt qua `PR_TRIAGE_<LOẠI>_TOKEN` trong `deploy/jenkins/.env`.

## Chưa kiểm chứng

Bộ chuyển đổi GitLab, Gitea, Bitbucket mới chạy với máy chủ giả theo tài liệu API, chưa với máy chủ thật (TD-8). Riêng Bitbucket Server, các đường REST ngoài webhook (merge-base, activities, raw) viết theo hiểu biết về API 1.0 chứ chưa đối chiếu được với trang tham chiếu chính thức.
