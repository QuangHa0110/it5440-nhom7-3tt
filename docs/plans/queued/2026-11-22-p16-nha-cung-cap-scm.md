# P16. Nhà cung cấp SCM: GitHub, GitLab, Gitea, Bitbucket Server

- **Status:** active
- **Người làm:** trinq (với Claude Code)
- **Đóng:** [ADR 0021](../../adr/0021-ho-tro-bon-may-chu-git-mot-lop-nha-cung-cap.md)
- **Quyết định cho phép:** ADR 0021
- **Nhánh:** `trinq/scm/providers`
- **Bắt đầu / Kết thúc:** 2026-11-22 / —

---

## Bối cảnh

Z dùng git nội bộ (loại chưa rõ) cộng GitHub thử nghiệm. Bot chỉ nói chuyện với GitHub. Xem ADR 0021.

## Ngoài phạm vi

- Không thử với máy chủ GitLab, Gitea, Bitbucket thật (không có trong môi trường). Chỉ test giả lập theo tài liệu API.
- Không có check run ngoài GitHub (ADR 0021 D5). Không cấu hình sẵn webhook Jenkins cho ngoài GitHub.
- Không đổi lược đồ lưu trữ.

## Hiện trạng đã kiểm chứng

- 2026-11-22: `make check` qua 349 test, 1 bỏ qua. Đối chiếu API GitLab và Gitea với tài liệu chính thức (một phần), Bitbucket chỉ đối chiếu được phần webhook.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `core/scm.py`: `ScmKind`, mã định danh repo, `PrInfo`, `OpenPr`, `GitRemote`, `Event`; `scm/provider.py` `ScmProvider` | `tests/core/test_scm.py` qua | — |
| T2 | `GitHubProvider` bọc bộ chuyển đổi hiện có | `tests/scm/test_github_provider.py` qua | T1 |
| T3 | `GitLabProvider` | `tests/scm/test_gitlab.py` qua | T1 |
| T4 | `GiteaProvider` | `tests/scm/test_gitea.py` qua | T1 |
| T5 | `BitbucketServerProvider` | `tests/scm/test_bitbucket.py` qua | T1 |
| T6 | `Settings`, `Services`, `handlers`, `server`, `GitFetcher` dùng provider; đường `/webhook/<kind>` | `tests/app/` qua, test đường mới qua | T2–T5 |
| T7 | CLI `publish`, `feedback`, `ci poll`, `ci fetch` dùng provider; Jenkinsfile gọi `ci fetch` | `tests/pipeline/test_cli_ci.py` qua | T2–T5 |
| T8 | Tài liệu `docs/scm-hosts.md`, nợ TD-8, cập nhật ADR 0018 bằng con trỏ | `make check` qua | T1–T7 |

## Cổng

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì khi xảy ra |
|---|---|---|
| API thật khác tài liệu hoặc khác phiên bản | Lỗi 404 hoặc thiếu trường khi chạy thật | Ghi vào devlog, sửa bộ chuyển đổi; test giả lập khóa hành vi đã biết |
| Máy chủ không cho lấy theo SHA | `git fetch` lỗi ở bước lấy mã | `GitFetcher` đã có dự phòng theo ref của PR |
| Tiền tố làm hỏng khớp mẫu cũ | Test `tests/core/test_delivery.py` đỏ | Giữ GitHub không tiền tố |
