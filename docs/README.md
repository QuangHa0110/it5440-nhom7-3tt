# `docs/` — mục lục tài liệu

| Đường dẫn | Nội dung |
|---|---|
| [Tài liệu đề tài](project/README.md) | Proposal hiện hành, tài liệu môn học, khảo sát và bản nháp |
| [architecture.md](architecture.md) | Thiết kế hệ thống, kèm sơ đồ PlantUML trong [diagrams/](diagrams/) |
| [github-app.md](github-app.md) | Cài đặt, cấu hình và vận hành GitHub App |
| [Jenkins](../deploy/jenkins/README.md) | Cài đặt và vận hành job quét PR nhiều repo |
| [scm-hosts.md](scm-hosts.md) | GitHub, GitLab, Gitea, Bitbucket Server: mã định danh repo, biến cấu hình, webhook, khác biệt |
| [demo.md](demo.md) | Kịch bản demo sáu PR |
| [huong-dan-chon-repo-va-pr.md](huong-dan-chon-repo-va-pr.md) | Tiêu chí và quy trình để thành viên chọn repo, PR và chạy ba cách A, B, C |
| [git-workflow.md](git-workflow.md) | Quy trình nhánh, PR, release, tag khóa cấu hình |
| [adr/](adr/) | Quyết định kiến trúc, chỉ thêm không sửa |
| [plans/](plans/) | Kế hoạch theo vòng đời `queued → active → done \| failed` |
| [test-records/](test-records/) | Hồ sơ kiểm thử thủ công theo ngày (kịch bản, kết quả, người test). Mã test tự động ở `tests/` |
| [devlog/](devlog/) | Phát hiện bất ngờ khi làm, và [sổ nợ](devlog/debt-ledger.md) |

**Quy tắc chọn nơi ghi:** quyết định đáng tranh luận → `adr/`; việc nhiều bước → `plans/`; điều bất ngờ → `devlog/`; nợ còn tồn → sổ nợ. Quy tắc chi tiết: mục "Tài liệu như mã" trong [../CLAUDE.md](../CLAUDE.md).
