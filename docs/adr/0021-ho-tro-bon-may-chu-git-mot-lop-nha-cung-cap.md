# ADR 0021 — Hỗ trợ GitHub, GitLab, Gitea và Bitbucket Server qua một lớp nhà cung cấp SCM

- **Status:** accepted (2026-11-22)
- **Người quyết định:** trinq (yêu cầu sản phẩm phải dùng được trên cả GitHub lẫn git nội bộ của Z, chưa biết loại nào, nên hỗ trợ cả ba loại phổ biến)
- **Liên quan:** thay phần tiền đề của [ADR 0018](0018-hai-duong-kich-hoat-mot-loi-moi-repo-mot-duong.md) ("Z dùng cả GitHub lẫn Jenkins": thực tế là GitHub và git nội bộ, còn Jenkins là nơi chạy), [ADR 0004](0004-cong-va-bo-chuyen-doi.md), [ADR 0012](0012-github-app-may-chu-va-hang-doi.md), [P16](../plans/done/2026-11-22-p16-nha-cung-cap-scm.md)

## Bối cảnh

- ADR 0018 trộn hai lớp khác nhau: nơi chứa mã (GitHub, git nội bộ) và đường kích hoạt (webhook, Jenkins). Z thật sự dùng một máy chủ git nội bộ (loại chưa biết), GitHub chỉ là bản thử của nhóm.
- Mọi bộ chuyển đổi hiện có chỉ nói chuyện với GitHub: `GitHubScm`, `GitHubApi`, `GitFetcher` (cố định `refs/pull/N/head`, tiêu đề `x-access-token`), xác thực chữ ký `X-Hub-Signature-256`, token cài đặt của GitHub App.
- Cổng `ScmPort` đã tách lõi khỏi GitHub (ADR 0004), nên thêm máy chủ khác không đụng lõi.

## Quyết định

- **D1. Một lớp nhà cung cấp.** `ScmProvider` (lớp trừu tượng) gom mọi thứ riêng của một máy chủ git: API đọc PR (`PrApiPort`), `ScmPort`, cấp token, địa chỉ và ref git, xác thực và phân tích webhook, liệt kê PR đang mở. Bốn cài đặt: `GitHubProvider`, `GitLabProvider`, `GiteaProvider`, `BitbucketServerProvider`. `handlers.py`, `server.py`, CLI và Jenkins chỉ nói chuyện với `ScmProvider`.
- **D2. Mã định danh repo có tiền tố kiểu máy chủ.** GitHub giữ nguyên `owner/repo` (tương thích mọi dữ liệu và cấu hình đang có). Các máy chủ khác dùng `gitlab:nhom/du-an`, `gitea:org/repo`, `bitbucket:KHOA/repo`. Lý do: cùng một `acme/web` có thể tồn tại trên hai máy chủ. Danh sách cho phép và `PR_TRIAGE_ROUTES` khớp trên chuỗi đầy đủ, nên mẫu `gitlab:acme/*` hoạt động không cần sửa `RepoGate`. Không đổi lược đồ lưu trữ.
- **D3. Cấu hình mỗi máy chủ bằng biến môi trường** `PR_TRIAGE_{GITLAB,GITEA,BITBUCKET}_{URL,TOKEN,WEBHOOK_SECRET,BOT_LOGIN}`. Token là mã truy cập tĩnh của một tài khoản bot (GitHub App vẫn dùng token cài đặt). Mọi bí mật bị che trong `repr` và log.
- **D4. Webhook có đường riêng** `POST /webhook/{gitlab,gitea,bitbucket}`; `POST /webhook` giữ nguyên cho GitHub. Xác thực theo từng máy chủ: GitHub `X-Hub-Signature-256` (HMAC), Gitea `X-Gitea-Signature` hoặc `X-Hub-Signature-256` (HMAC), Bitbucket `X-Hub-Signature` (HMAC), GitLab `X-Gitlab-Token` (so sánh thời gian hằng).
- **D5. Check run chỉ có trên GitHub.** GitLab, Gitea, Bitbucket không có kết luận `neutral` kèm chú thích theo dòng tương đương, nên `upsert_check` là no-op (trả chuỗi rỗng) ở đó. Comment vẫn là kênh chính (ADR 0014).
- **D6. Jenkins dùng chung lớp này.** `pr-triage ci poll` hỏi PR đang mở qua provider; `pr-triage ci fetch` lấy mã qua provider (thay đoạn shell cố định GitHub). Webhook Jenkins (Generic Webhook Trigger) vẫn chỉ cấu hình sẵn cho GitHub; các máy chủ khác dùng poll hoặc webhook của máy chủ pr-triage.

## Phương án khác

- **Một repo cho mỗi loại máy chủ (fork):** nhân đôi mã lõi.
- **Chỉ đoán một loại (GitLab):** sai thì phí công; ba loại chiếm gần hết thị trường tự lưu trữ.
- **Gom về một ID số duy nhất cho repo:** cần đổi lược đồ lưu trữ và dữ liệu cũ.

## Hệ quả

- **Tốt hơn:** thêm loại máy chủ thứ năm chỉ cần một lớp con; lõi không đổi; GitHub không đổi hành vi.
- **Tệ hơn:** ba bộ chuyển đổi mới chưa được thử với máy chủ thật, chỉ có test giả lập theo tài liệu API (ghi ở TD-8). Chi tiết API Bitbucket Server chưa đối chiếu được với tài liệu chính thức vì không tải được trang tham chiếu REST.
- **Từ nay phải đúng:** mọi mã mới nhận `repo` là mã định danh đầy đủ (có tiền tố), không tự tách `owner/repo`; dùng `core.scm.split_repo`. Không thêm tên máy chủ nội bộ của Z vào repo (repo là public).
