# P13. Jenkins: một job trung tâm quét PR của nhiều repo, có danh sách cho phép

- **Status:** done
- **Người làm:** hadvq (với Claude Code)
- **Đóng:** —
- **Quyết định cho phép:** nhóm chọn "cách 1" ngày 2026-11-17: job trung tâm + webhook cấp tổ chức + danh sách repo cho phép
- **Nhánh:** `hadvq/deploy/jenkins-central-job`
- **Bắt đầu / Kết thúc:** 2026-11-17 / 2026-11-17

---

## Bối cảnh

Bản Jenkins cục bộ đầu tiên (`deploy/jenkins/`) dùng một multibranch job cho đúng một repo (`GITHUB_REPO`)
và đòi chép `Jenkinsfile` vào repo được quét. Công ty Z có nhiều repo, mỗi repo đã có `Jenkinsfile` riêng,
nên cách này không mở rộng được: phải sửa từng repo, không tắt bot ở một chỗ được.

## Ngoài phạm vi

- Không tách ba job theo quyền như ADR 0007 (vẫn một container giữ mọi secret, như bản đầu).
- Không thêm job `feedback` định kỳ.
- Không đổi mã trong `src/`. Không hỗ trợ GitLab hay Bitbucket.

## Hiện trạng đã kiểm chứng

- 2026-11-17: `src/pr_triage/app/settings.py` đã có `PR_TRIAGE_ALLOWED_REPOS` khớp mẫu bằng `fnmatchcase`, không phân biệt hoa thường. Dùng lại cùng quy ước.
- Image `pr-triage-jenkins:local` build được, `pr-triage run` chạy được trong container trên repo demo.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `triage.Jenkinsfile`: job có tham số `REPO`, `PR`, `BASE_REF`, `HEAD_SHA`, kiểm tra danh sách cho phép, tự fetch repo, chạy `run` rồi `publish` | Build tay với một repo ngoài danh sách ra `NOT_BUILT`; với repo trong danh sách chạy đủ hai stage | — |
| T2 | Webhook cấp tổ chức qua Generic Webhook Trigger, khai báo trong `casc.yaml` | Job sau khi khởi động có trigger với token lấy từ credential `webhook-token` | T1 |
| T3 | `poll.Jenkinsfile` + `poll_prs.py`: hỏi GitHub định kỳ PR đang mở của các repo cho phép, kích job T1 khi đầu PR đổi | Lần chạy thứ hai không kích lại PR chưa đổi | T1 |
| T4 | Cập nhật `casc.yaml`, `plugins.txt`, `Dockerfile`, `.env.example`, README | `docker compose up` tạo đủ hai job, README không còn `GITHUB_REPO` | T1–T3 |

## Cổng

```bash
docker compose -f deploy/jenkins/docker-compose.yml up -d --build
```

Đăng nhập được, có hai job `pr-triage` và `pr-triage-poll`, build tay `pr-triage` với repo ngoài danh sách ra `NOT_BUILT`.

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì khi xảy ra |
|---|---|---|
| Job DSL trong JCasC không đọc được file Jenkinsfile | Log khởi động có lỗi seed job | Nhúng script qua `${readFile:...}` của JCasC |
| Sandbox Groovy chặn hàm dùng trong `poll.Jenkinsfile` | Build lỗi `RejectedAccessException` | Đổi sang hàm có trong danh sách cho phép, hoặc xử lý trong script Python |
| Nhiều build ghi SQLite cùng lúc | `database is locked` | Job `pr-triage` không chạy song song (`disableConcurrentBuilds`) |

---

## Kết quả

*Điền khi đóng kế hoạch. Không sửa phần thân phía trên.*

- **Kết quả (2026-11-17, Jenkins trong Docker, 1 repo Java riêng tư có 2 PR mở):**
  - JCasC tạo đủ hai job; Job DSL đọc được Jenkinsfile bằng `new File(...)`, không lỗi sandbox.
  - Webhook giả lập: token sai trả 404, PR nháp không kích, repo ngoài danh sách ra `NOT_BUILT`.
  - `pr-triage-poll` kích đúng 2 PR một lần, các lần sau "kích 0 PR".
  - Hai build chạy trọn `run` + `publish` ở chế độ shadow, 0 cảnh báo mới, comment in ra console.
- **Khác kế hoạch ở đâu:**
  - `disableConcurrentBuilds()` trong Jenkinsfile không có hiệu lực ở build đầu tiên: hai build đầu chạy song song (workspace `pr-triage@2`). Khai báo thêm trong `casc.yaml`, kiểm tra lại thì chạy nối tiếp.
  - `publish --post` ở chế độ shadow không in gì; Jenkinsfile chỉ thêm `--post` khi mode là `comment`.
  - Image build lúc ổ C: đầy chứa plugin 0 byte nằm trong cache; phải `docker builder prune` rồi build `--no-cache`.
- **Chưa kiểm chứng:** đường gọi LLM (khóa trống, PR không có cảnh báo), đăng comment thật ở mode `comment`, webhook thật từ GitHub.
- **Ghi ở:** README `deploy/jenkins/`
