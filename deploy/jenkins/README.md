# Chạy pr-triage trên Jenkins cục bộ

Mục tiêu: dựng một Jenkins trên máy mình, đóng vai CI của công ty, để bot quét PR của **nhiều repo** GitHub và đăng comment.

Bot là **một job trung tâm** `pr-triage`. Repo được quét không cần thêm `Jenkinsfile` hay sửa gì. Repo nào được quét do
**một danh sách cho phép** quyết định (`PR_TRIAGE_ALLOWED_REPOS`), nên bật, tắt hay thêm repo chỉ cần sửa một dòng.

```
                    ┌─ ở công ty: webhook cấp tổ chức (sự kiện pull_request) ─┐
GitHub (mọi repo) ──┤                                                         ├──► job pr-triage (REPO, PR, BASE_REF, HEAD_SHA)
                    └─ trên máy cá nhân: job pr-triage-poll hỏi mỗi 2 phút ───┘        │ repo ngoài danh sách cho phép → NOT_BUILT
                                                                                       │ fetch nhánh đích + refs/pull/N/head
        comment ◄──────────────────────────────────────────────────────────────────────┘ pr-triage run → pr-triage publish
```

Webhook từ GitHub không tới được `localhost`, nên khi chạy trên máy cá nhân dùng job hỏi định kỳ `pr-triage-poll`.
Cả hai đường đều kích cùng một job `pr-triage` với cùng tham số.

## Thư mục này có gì

| File | Vai trò |
|---|---|
| `Dockerfile` | Image Jenkins LTS đã cài sẵn `pr-triage`, Semgrep 1.185.0, Python 3.12 |
| `plugins.txt` | Plugin Jenkins cần dùng, có Generic Webhook Trigger |
| `casc.yaml` | Cấu hình Jenkins dạng mã: tài khoản admin, credential, hai job, tham số và webhook |
| `triage.Jenkinsfile` | Pipeline của job `pr-triage`: kiểm tra danh sách cho phép, fetch, `run`, `publish` |
| `poll.Jenkinsfile` | Pipeline của job `pr-triage-poll`: tìm PR mới hoặc có commit mới, kích `pr-triage` |
| (lệnh `pr-triage ci`) | `ci allowed` kiểm tra danh sách cho phép và định tuyến, `ci poll` hỏi PR đang mở qua GitHub API. Mã ở `src/pr_triage/triggers/`, có test |
| `docker-compose.yml` | Chạy Jenkins ở cổng 8081, dữ liệu bot lưu ở volume `triage_data` |
| `.env.example` | Mẫu biến môi trường, sao chép thành `.env` |

## Bước 1. Chọn repo được quét

Dùng repo GitHub **của bạn** có PR đang mở, hoặc repo mà chủ repo đã đồng ý. Repo nên là Java: luật quét hiện chỉ phủ SQL
injection trên Java và secret viết cứng. Repo khác vẫn chạy được, nhưng gần như luôn ra "không có cảnh báo mới".

- Chưa có repo phù hợp thì dựng repo demo 6 PR (xem [docs/demo.md](../../docs/demo.md)). Trên Windows đặt `PYTHONIOENCODING=utf-8` trước khi chạy `scripts/demo_repo.py`.
- **Không** cần chép file nào vào repo. Nếu trước đây đã chép `Jenkinsfile` của bản cũ vào repo thì có thể xóa đi.

## Bước 2. Tạo token GitHub

GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token:

- **Repository access:** Only select repositories → chọn **mọi** repo sẽ ghi vào danh sách cho phép.
- **Permissions:** Contents: Read-only; Pull requests: Read and write (để đăng comment); Metadata: Read-only (tự bật).

Không cần quyền Commit statuses: job trung tâm không báo trạng thái build lên PR.
Không dán token vào chat, issue hay commit. Chỉ để trong `deploy/jenkins/.env`.

## Bước 3. Chọn LLM

Bot gọi LLM qua API kiểu OpenAI. Từ trong container, máy Windows là `host.docker.internal`.

| Lựa chọn | `PR_TRIAGE_LLM_BASE_URL` | Ghi chú |
|---|---|---|
| Ollama, 9router... chạy trên máy Windows | `http://host.docker.internal:<cổng>/v1` | Đặt `PR_TRIAGE_LLM_ALLOW_EXTERNAL=1`: bot chỉ coi `localhost` là nội bộ |
| Dịch vụ cloud tương thích OpenAI | URL của dịch vụ, kết thúc bằng `/v1` | Đặt `ALLOW_EXTERNAL=1` **chỉ khi** mã là của bạn, mã nguồn mở, hoặc công ty đã đồng ý bằng văn bản |

Một gateway chạy trên máy nhưng chuyển tiếp tới mô hình cloud vẫn là gửi mã ra ngoài.
Không có LLM, bot vẫn quét và comment, nhưng cách B và C ra `unknown` và comment ghi "Một số bước chưa hoàn tất".

## Bước 4. Điền `.env` và khởi động

```bash
cp deploy/jenkins/.env.example deploy/jenkins/.env
```

Mở `deploy/jenkins/.env` và điền:

| Biến | Giá trị |
|---|---|
| `JENKINS_ADMIN_PASSWORD` | Mật khẩu đăng nhập `admin` |
| `PR_TRIAGE_ROUTES` | Tuỳ chọn. `jenkins:owner/repo-*,github-app:owner/web-*`: mỗi repo chỉ một đường. **Bắt buộc đặt khi GitHub App cùng chạy trên tổ chức này** (ADR 0018) |
| `PR_TRIAGE_ALLOWED_REPOS` | `owner/repo1,owner/repo2`. **Để trống thì bot không quét gì** |
| `GITHUB_TOKEN` | Token ở bước 2 |
| `PR_TRIAGE_WEBHOOK_TOKEN` | Chuỗi ngẫu nhiên, ví dụ `openssl rand -hex 16`. Bắt buộc có, kể cả khi chưa dùng webhook |
| `PR_TRIAGE_POLL` | `1` trên máy cá nhân |
| Biến `PR_TRIAGE_LLM_*` | Theo bước 3 |
| `PR_TRIAGE_MODE` | `shadow` cho lần chạy đầu |

```bash
docker compose -f deploy/jenkins/docker-compose.yml up -d --build
```

Lần đầu build mất khoảng 5 phút và cần vài GB trống trên ổ chứa dữ liệu Docker Desktop (thường là C:).
Mở http://localhost:8081, đăng nhập `admin` với mật khẩu trong `.env`.

## Bước 5. Chạy và xem kết quả

1. Có hai job: **pr-triage** và **pr-triage-poll**. Trong vòng 2 phút, `pr-triage-poll` chạy lần đầu và kích `pr-triage`
   cho **mọi PR đang mở** (trừ bản nháp) của các repo trong danh sách. Sau đó chỉ kích lại khi PR có commit mới.
   Muốn nhanh thì vào `pr-triage-poll` → **Build Now**.
2. Mỗi build của `pr-triage` mang tên `#số owner/repo#PR`. Build ra `NOT_BUILT` (xám) nghĩa là repo không có trong danh sách cho phép.
3. Mở một build → **Console Output**. Dòng JSON sau `pr-triage run` là tóm tắt:
   `{"new_findings": 1, "verdicts": {"A:likely_true": 1, "B:...": 1, "C:...": 1}, "tokens_in": ..., "duration_s": ...}`
4. Ở chế độ `shadow`, stage `publish` in comment ra console nhưng **không** đăng lên PR. Kết quả đầy đủ nằm trong artifact `out/triage-result.json`.

**Quét một PR bất kỳ bằng tay:** vào `pr-triage` → **Build with Parameters**, điền `REPO` (`owner/repo`) và `PR` (số).
Để trống `BASE_REF` thì dùng nhánh mặc định của repo; để trống `HEAD_SHA` thì dùng đầu nhánh PR hiện tại.
Repo vẫn phải có trong danh sách cho phép.

## Bước 6. Bật comment lên PR

1. Sửa `.env`: `PR_TRIAGE_MODE=comment`.
2. Khởi động lại để Jenkins nhận biến mới:

   ```bash
   docker compose -f deploy/jenkins/docker-compose.yml up -d
   ```

3. Build lại một PR bằng tay (Build with Parameters) hoặc push commit mới lên PR. Comment của bot xuất hiện trên PR.
   Mỗi lần có commit mới, bot **cập nhật** comment cũ thay vì đăng thêm.
4. Thử phản hồi: trả lời comment bằng `fp <mã>` hoặc `tp <mã>`.

Thêm hay bớt repo: sửa `PR_TRIAGE_ALLOWED_REPOS`, nhớ cấp quyền cho token trên repo mới, rồi chạy lại `up -d`.

## Bước 7. Lấy dữ liệu ra để tính số liệu

Mọi lượt chạy của mọi repo được lưu chung trong `/data/store.sqlite` của container (volume `triage_data`),
phân biệt bằng tên repo. Job `pr-triage` không chạy song song nên không tranh nhau ghi SQLite.

```bash
docker compose -f deploy/jenkins/docker-compose.yml cp jenkins:/data ./data/jenkins
```

Sau đó dùng các lệnh `pr-triage eval ... --db data/jenkins/store.sqlite` như bình thường. Thư mục `data/` không được commit.

## Dừng và dọn

```bash
docker compose -f deploy/jenkins/docker-compose.yml down
```

`down` giữ nguyên dữ liệu. Thêm `-v` sẽ **xóa** cả cấu hình Jenkins, `store.sqlite` và trạng thái của job hỏi định kỳ
(lần sau bật lên sẽ quét lại mọi PR đang mở).

## Triển khai ở công ty

Cùng image và cùng hai Jenkinsfile, chỉ khác cách kích:

1. Jenkins của công ty phải nhận được request từ GitHub (hoặc từ hệ thống quản lý mã nội bộ).
2. Admin tổ chức tạo **webhook cấp tổ chức**: Organization → Settings → Webhooks → Add webhook.
   - Payload URL: `https://<jenkins>/generic-webhook-trigger/invoke?token=<PR_TRIAGE_WEBHOOK_TOKEN>`
   - Content type: `application/json`. Chỉ chọn sự kiện **Pull requests**.
3. Đặt `PR_TRIAGE_POLL=0` để tắt job hỏi định kỳ, tránh quét trùng.
4. `PR_TRIAGE_ALLOWED_REPOS` liệt kê đúng các repo mà team đã đồng ý. Danh sách này đồng thời là hồ sơ đồng thuận.
   Webhook chấp nhận mẫu như `org/payment-*`; job hỏi định kỳ chỉ nhận tên đầy đủ.
5. Thay token cá nhân bằng tài khoản bot hoặc token của GitHub App, chỉ có quyền trên các repo cho phép.

Webhook chỉ kích build với sự kiện `opened`, `synchronize`, `reopened`, `ready_for_review` của PR không phải bản nháp.
Tắt toàn bộ bot khẩn cấp: xóa danh sách cho phép, hoặc vào job `pr-triage` → Disable Project.

## Gặp lỗi

| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| `up --build` báo `input/output error` | Ổ chứa dữ liệu Docker Desktop đã đầy. Dọn chỗ trống rồi khởi động lại Docker Desktop |
| `pr-triage-poll` kích 0 PR | `PR_TRIAGE_ALLOWED_REPOS` trống hoặc ghi sai tên, PR đều là bản nháp, hoặc đã quét rồi và chưa có commit mới. Console có dòng tóm tắt "N repo, M PR cần quét" |
| Console của poll có `HTTP 401/403/404` | Token sai, hết hạn, hoặc chưa cấp quyền cho repo đó |
| Build `pr-triage` ra `NOT_BUILT` | Repo không có trong danh sách cho phép, hoặc `REPO`/`PR` sai định dạng |
| Stage `triage` đỏ, log `git fetch` lỗi | Token không đọc được repo, hoặc số PR không tồn tại |
| Kết quả `B:unknown`, `C:unknown`, `tokens_in: 0` | Không gọi được LLM: sai URL, sai model, thiếu khóa, hoặc thiếu `ALLOW_EXTERNAL=1` khi URL không phải `localhost` |
| Comment luôn là "không có cảnh báo mới" | Repo không phải Java, hoặc PR không đụng tới truy vấn SQL hay secret |
| Đổi `.env` mà không có tác dụng | Chạy lại `up -d` để tạo lại container |

## Còn khác gì so với thiết kế đầy đủ

- **Phân quyền chưa đúng ADR 0007.** Mọi stage chạy chung một container, có cả token GitHub lẫn khóa LLM.
  Ở công ty, mỗi stage nên chạy trong một agent riêng, chỉ nhận đúng credential của nó.
- **Chưa có job `feedback` định kỳ** để thu `fp`/`tp` và phát hiện cảnh báo đã sửa. Lệnh `pr-triage feedback` có sẵn nhưng cần `--comment-ref` từ lượt `publish`.
- **Lệnh `publish` chưa tạo check run**, chỉ đăng comment. GitHub App thì có.
- **Mọi build chạy nối tiếp** để giữ an toàn cho SQLite. Nhiều repo nhiều PR thì hàng đợi dài; muốn song song cần kho dữ liệu khác SQLite.
- Chỉ dùng được với GitHub. GitLab hay Bitbucket cần thêm một bộ chuyển đổi cho `ScmPort`, và đổi đường dẫn JSON trong webhook.
