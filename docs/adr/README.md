# `docs/adr/` — Architecture Decision Records

Mỗi file là một quyết định đáng tranh luận. Tên file: `NNNN-tieu-de-viet-khong-dau.md`, số thứ tự liên tục, không bỏ số.

- **Chỉ thêm, không sửa.** Muốn đổi quyết định thì viết ADR mới, đặt `Status: supersedes NNNN` và thêm một dòng con trỏ vào ADR cũ.
- Bắt đầu từ [_template.md](_template.md). Kiểm tra `ls | tail -1` trước khi lấy số mới.

| ADR | Quyết định | Trạng thái |
|---|---|---|
| [0001](0001-mo-hinh-nhanh-va-release.md) | Mô hình nhánh `main`/`dev`/nhánh cá nhân, release bằng tag và bump-my-version | accepted |
| [0002](0002-cau-truc-repo-theo-package.md) | Cấu trúc repo theo package Python, tách mã, cấu hình, dữ liệu, báo cáo, tài liệu | accepted |
| [0003](0003-llm-goi-mot-lan-khong-dung-agent.md) | LLM nhận định bằng một lần gọi, không dùng vòng lặp agent | accepted |
| [0004](0004-cong-va-bo-chuyen-doi.md) | Cổng và bộ chuyển đổi, ba gói nền core, store, pipeline | accepted |
| [0005](0005-dung-lai-ma-nguon-mo.md) | Dùng lại mã nguồn mở ở tầng công cụ, không fork bot có sẵn | accepted |
| [0006](0006-luu-tru-sqlite-va-blob.md) | SQLite (WAL) và kho blob trong vùng của Z | accepted |
| [0007](0007-ba-job-tach-quyen.md) | Ba job CI với ba mức quyền | accepted |
| [0008](0008-llm-gateway-openai-compat-va-bi-mat.md) | API kiểu OpenAI, cấu hình bằng biến môi trường, khóa không vào repo | accepted |
| [0009](0009-langgraph-dieu-phoi-do-thi-nhan-dinh.md) | LangGraph điều phối đồ thị nhận định, không làm agent tự do | accepted |
| [0010](0010-phan-hoi-theo-tung-canh-bao.md) | Phản hồi theo từng cảnh báo bằng lệnh fp và tp | accepted |
| [0011](0011-dau-van-tay-va-so-head-base.md) | Dấu vân tay không dùng số dòng, cảnh báo mới là head trừ base | accepted |
| [0012](0012-github-app-may-chu-va-hang-doi.md) | GitHub App: máy chủ webhook, token cài đặt, hàng đợi bền, cấu hình từ nhánh đích | accepted |
| [0013](0013-quet-secret-tich-hop.md) | Quét secret tích hợp, giá trị bị che từ lúc phát hiện | accepted |
| [0014](0014-phan-hoi-theo-vai-tro-va-cc.md) | Phản hồi theo vai trò, chính sách CC, làm sạch nội dung do mô hình sinh | accepted |
| [0015](0015-danh-gia-ma-nguon-mo-nhan-ai.md) | Đợt 1: đánh giá trên mã Java mã nguồn mở, nhãn tham chiếu AI (ngoại lệ của quy tắc không dùng AI gán nhãn) | accepted |
| [0016](0016-quet-moc-lich-su-tach-tap-theo-repo.md) | Đợt 1: quét mốc lịch sử của 6 repo, tách dev/eval theo nguyên repo (thay một phần D1 của 0015) | accepted |
| [0017](0017-kiem-dinh-bang-subagent-thay-nguoi.md) | Đợt 1: kiểm định 50 ca eval bằng subagent AI độc lập thay người (thay một phần D2 của 0015) | accepted |
| [0018](0018-hai-duong-kich-hoat-mot-loi-moi-repo-mot-duong.md) | Hai đường kích hoạt (GitHub App, Jenkins) dùng chung một lõi, mỗi repo chỉ một đường | accepted |
| [0019](0019-bo-luat-semgrep-p-default-khoa-bang-ma-bam.md) | Bộ luật Semgrep `p/default`, tải trong hạ tầng chạy bot, khóa bằng mã băm, không commit luật | accepted |
| [0020](0020-gui-ma-cua-z-len-llm-cloud.md) | Dùng LLM cloud cho mã của Z, cần văn bản, che secret, gửi tối thiểu, có trần chi phí | accepted |
| [0021](0021-ho-tro-bon-may-chu-git-mot-lop-nha-cung-cap.md) | Hỗ trợ GitHub, GitLab, Gitea, Bitbucket Server qua một lớp nhà cung cấp SCM | accepted |
