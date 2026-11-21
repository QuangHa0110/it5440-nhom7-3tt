# ADR 0018 — Hai đường kích hoạt (GitHub App, Jenkins) dùng chung một lõi, mỗi repo chỉ một đường

- **Status:** accepted (2026-11-20)
- **Người quyết định:** trinq (chọn giữ cả hai đường ngày 2026-11-20; Z dùng cả GitHub lẫn Jenkins)
- **Liên quan:** [ADR 0004](0004-cong-va-bo-chuyen-doi.md), [ADR 0007](0007-ba-job-tach-quyen.md), [ADR 0012](0012-github-app-may-chu-va-hang-doi.md), [P13](../plans/done/2026-11-17-p13-jenkins-job-trung-tam-nhieu-repo.md), [P14](../plans/done/2026-11-20-p14-hai-duong-kich-hoat-huong-doi-tuong.md)

> Số 0018 bỏ qua 0015 đến 0017: ba ADR đó của đợt đánh giá nguồn mở đang nằm ngoài repo (xem hồ sơ kiểm thử 2026-11-18), để khi đưa vào không trùng số.

## Bối cảnh

Hai đường kích hoạt cùng tồn tại: GitHub App (`pr-triage serve`, ADR 0012) và Jenkins (job trung tâm, P13). Trước thay đổi này:

- Danh sách repo cho phép được viết hai lần với hai nghĩa khác nhau: `Settings.repo_allowed` (rỗng = cho mọi repo) và `deploy/jenkins/ci_helper.py` (rỗng = không repo nào). Hai bản chép tay dễ lệch.
- Logic của đường Jenkins (kiểm tra tham số, poll) nằm ngoài package, không có test, không dùng chung kiểu dữ liệu với App.
- Không có gì ngăn một repo vừa cài App vừa nằm trong danh sách Jenkins. Khi đó một PR bị quét hai lần, comment hai lần, hai tiến trình ghi chung SQLite.

## Quyết định

- **D1. Một kiểu yêu cầu chung.** `ScanRequest` (repo, PR, SHA đầu nhánh, nhánh đích, kênh) là thứ lõi nhìn thấy. Lõi không biết yêu cầu đến từ webhook hay từ tham số Jenkins.
- **D2. Mỗi đường là một lớp con của `Trigger`.** `Trigger` là lớp trừu tượng có phương thức mẫu `collect()` (phân tích, rồi lọc qua cổng repo). Lớp con chỉ cài đặt `parse()`: `GitHubWebhookTrigger`, `JenkinsParamsTrigger`, `PollTrigger`.
- **D3. Một danh sách repo cho phép.** `RepoAllowList` thay cả hai bản chép. Nghĩa của "rỗng" là tham số tường minh, không phải hành vi ngầm: App giữ `rỗng = mọi repo` (tương thích), Jenkins dùng `rỗng = không repo nào`, vì webhook cấp tổ chức gửi sự kiện của mọi repo.
- **D4. Mỗi repo một đường.** `PR_TRIAGE_ROUTES` (`kênh:mẫu,...`, kênh là `github-app` hoặc `jenkins`) gán repo cho đúng một kênh. Không đặt biến này thì mọi kênh đều được (giữ hành vi cũ). Đã đặt thì: repo không khớp mẫu nào bị từ chối; repo khớp mẫu của hai kênh khác nhau bị từ chối ở cả hai (đóng khi gặp mơ hồ); cùng một mẫu gán cho hai kênh là lỗi cấu hình ngay khi nạp.
- **D5. Đăng kết quả qua đa hình.** `ResultSink` có hai cài đặt: `ConsoleSink` (shadow, chạy thử: chỉ in) và `ScmSink` (đăng thật qua `Publisher`). Nơi gọi chọn sink một lần, không rải `if mode`.
- **D6. Logic Jenkins vào package, Jenkinsfile mỏng.** `ci_helper.py` bị thay bằng `pr-triage ci allowed` và `pr-triage ci poll`, có test. Jenkinsfile chỉ gọi lệnh.

## Phương án khác

- **Bỏ một đường:** đơn giản hơn nhưng Z dùng cả hai.
- **Để hai đường tự phối hợp bằng khóa trong SQLite:** chống quét đôi nhưng phải vận hành một kho chung giữa hai tiến trình; cấu hình tĩnh D4 đơn giản và kiểm tra được trước khi chạy.
- **Cho `rỗng` của danh sách có cùng một nghĩa ở mọi nơi:** đổi hành vi App đang có người dùng, hoặc mở toang Jenkins. Tham số tường minh an toàn hơn.

## Hệ quả

- **Tốt hơn:** thêm đường thứ ba (GitLab, Actions) chỉ cần một lớp con; hai đường không thể quét đôi cùng một repo nếu `PR_TRIAGE_ROUTES` đặt đúng; test được toàn bộ logic Jenkins.
- **Tệ hơn:** thêm một biến cấu hình; Jenkinsfile phụ thuộc `pr-triage` có trong image (đã đúng từ P13).
- **Từ nay phải đúng:** khi cả hai đường bật cho cùng một tổ chức thì phải đặt `PR_TRIAGE_ROUTES`. Hai đường vẫn dùng chung SQLite nếu trỏ cùng `PR_TRIAGE_DB`; ADR này không giải quyết chuyện đó, chỉ đảm bảo không cùng một repo.
- **Không đổi:** ADR 0007 (tách quyền) chưa được áp dụng cho Jenkins. Đó vẫn là nợ (TD-5).
