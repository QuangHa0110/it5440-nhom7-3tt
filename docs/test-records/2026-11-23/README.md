# 2026-11-23 — E2E trên Gitea, GitLab CE và Jenkins

Chạy sáu kịch bản demo trên từng SCM thật và một job Jenkins dùng Gitea với LLM tự host. Xem [báo cáo kết quả](results/e2e-scm-and-jenkins.md) để biết cấu hình, lỗi phát hiện và giới hạn của lần chạy.

## Ảnh minh chứng

- [Gitea PR #1](results/screenshots/01-gitea-pr-1.png) có comment của bot và phản hồi thử nghiệm.
- [GitLab MR !1](results/screenshots/02-gitlab-mr-1.png) có comment của bot và phản hồi `fp`/`tp`.
- [Jenkins poll #6](results/screenshots/03-jenkins-poll-6.png) tìm được PR cần quét và kích hoạt job.
- [Jenkins triage #2](results/screenshots/04-jenkins-triage-2.png) fetch đúng commit, quét với LLM và cập nhật comment thành công.
