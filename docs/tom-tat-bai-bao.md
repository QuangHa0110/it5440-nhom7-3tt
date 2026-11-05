# Tóm tắt 4 bài báo của đề tài 3

PDF tải theo link trong [papers/README.md](papers/README.md). Số liệu dưới đây lấy từ phần tóm tắt và phần đánh giá của từng bài.

## 1. An Empirical Security Analysis of Open-Source Software Used in Onboard Satellite Systems

R. Idan, T. Cohen Galor, A. Shabtai, Y. Elovici (Ben-Gurion University), 09/2026, arXiv:2609.15425.

**Bài toán.** Phần mềm mã nguồn mở được dùng ngày càng nhiều trong phần mềm bay của vệ tinh, nơi việc vá lỗi rất tốn kém. Hiện chưa có số liệu thực nghiệm về rủi ro bảo mật của nhóm phần mềm này.

**Cách làm.**
- Quét 126 repo công khai bằng một quy trình gồm nhiều lớp:
  - SBOM: Syft (CycloneDX).
  - SCA: Grype, Trivy, OSV-Scanner, OWASP Dependency-Check.
  - SAST: Semgrep (bộ luật `auto`), CodeQL, Bandit cho Python, Cppcheck cho C/C++.
  - IaC: Checkov.
  - Secret: Gitleaks.
- Làm sạch theo luật: bỏ kết quả mang tính thông tin, mã sinh tự động, metadata.
- Lọc theo phạm vi: bỏ mã mặt đất, tài liệu, ví dụ, mô phỏng. Các quyết định chưa rõ ràng được ghi lại có kiểm soát phiên bản.
- Khử trùng lặp bằng "dấu vân tay" riêng cho từng lớp:
  - SCA: repo + tên gói + phiên bản + mã lỗ hổng.
  - SAST/IaC/secret: repo + vị trí + mã luật/CWE + ngữ cảnh.
  - Khi nhiều công cụ cùng báo một phát hiện thì giữ mức nghiêm trọng cao nhất.
- Phân loại theo CWE (8 họ điểm yếu) và OWASP.

**Kết quả.**
- Còn lại 2,827 phát hiện. 49% ở mức trung bình; 72% từ mức trung bình trở lên.
- Nhiều nhất là An toàn bộ nhớ và Chất lượng mã, sau đó là Kiểm tra đầu vào và Chèn mã.
- 81.4% phát hiện nằm trong mã do dự án tự viết, phần còn lại thuộc thư viện phụ thuộc.
- Gán nhãn tay 360 mẫu ngẫu nhiên: **22.2% là cảnh báo sai** (khoảng tin cậy 95%: 17.6–27.6%).
- Riêng Cppcheck đóng góp 1,483/2,827 phát hiện. Bỏ Cppcheck ra thì "Chèn mã" trở thành nhóm lớn nhất (35.9%), nên bài có thêm phân tích độ nhạy theo từng công cụ.

## 2. QLCoder: A Query Synthesizer for Static Analysis of Security Vulnerabilities

C. Wang, Z. Li, S. Dutta, M. Naik, ICLR 2026, arXiv:2511.08462. Mã nguồn: https://github.com/neuralprogram/qlcoder

**Bài toán.** Viết truy vấn CodeQL để phát hiện một lỗ hổng cụ thể đòi hỏi vừa giỏi bảo mật vừa giỏi phân tích chương trình. Bộ truy vấn mặc định thì phủ ít loại lỗi và báo sai nhiều.

**Cách làm.**
- Agent LLM (xây trên Claude Code) nhận thông tin CVE và tự viết truy vấn CodeQL.
- Vòng lặp có phản hồi từ việc chạy truy vấn.
- Qua giao diện MCP, agent dùng thêm Language Server (để viết đúng cú pháp) và cơ sở dữ liệu RAG (truy vấn mẫu và tài liệu).
- Truy vấn được coi là **đúng** nếu phát hiện lỗi trên phiên bản có lỗ hổng và **không** báo trên phiên bản đã vá.

**Kết quả.**
- Thử trên 176 CVE thuộc 111 dự án Java: 53.4% truy vấn đúng. Dùng Claude Code không có các thành phần này chỉ đạt 10%.
- F1 = 0.7, so với 0.048 của IRIS và 0.073 của bộ truy vấn mặc định của CodeQL.

## 3. Contextualizing Sink Knowledge for Java Vulnerability Discovery (GONDAR)

F. Fleischer, C. Zhang và cộng sự (Georgia Tech, Samsung Research, U. Waterloo), arXiv:2604.01645.

**Bài toán.** Lỗ hổng Java thường xuất hiện tại các "sink", tức là các API nhạy cảm như `Runtime.exec()`, thao tác file, giải tuần tự hóa. Các fuzzer hiện nay không tận dụng hiểu biết về những sink này.

**Cách làm.**
- Quét theo CWE để tìm các vị trí gọi sink, rồi dùng LLM lọc tĩnh để giữ lại những sink thật sự với tới được và khai thác được.
- Hai agent phối hợp với fuzzer có hướng dẫn bởi độ phủ:
  - Agent khám phá: giải ràng buộc đường đi để đi tới sink.
  - Agent khai thác: sinh exploit thỏa điều kiện kích hoạt lỗ hổng.

**Kết quả.**
- Tìm được gấp 4 lần số lỗ hổng so với Jazzer.
- Một phiên bản trước của GONDAR góp phần vào hệ thống của đội vô địch DARPA AI Cyber Challenge.
- Được tích hợp vào OSS-CRS (OpenSSF) và đã tìm được một lỗ hổng zero-day.

## 4. P2Patch: Exploit-Guided Vulnerability Repair

M. Iranmanesh, S. Moradi Sabet và cộng sự (Simon Fraser University và cộng sự), 10/2026, arXiv:2610.20245. Mã nguồn: https://github.com/P2Patch/P2patch

**Bài toán.** Các hệ thống sửa lỗ hổng tự động thường kiểm tra bản vá bằng **chính bằng chứng đã dùng để tạo ra nó** (cảnh báo tĩnh, vết sanitizer, exploit đã biết, bộ test). Bài gọi đây là vấn đề *dùng lại oracle*: bản vá chặn được đúng một exploit thì trông như thành công, nhưng vẫn có thể bị một biến thể khác của cùng lỗ hổng vượt qua.

**Cách làm.**
- Vòng lặp đối kháng giữa hai agent:
  1. Agent tấn công dựng exploit tái hiện lỗi (PoV).
  2. Agent sửa vá chương trình.
  3. Agent tấn công tìm một exploit khác vượt qua bản vá.
- Mọi exploit tìm được đều trở thành yêu cầu mà bản vá cuối cùng phải chặn.
- Bộ oracle dùng để đánh giá được giữ tách biệt hoàn toàn với các exploit dùng trong lúc sửa.

**Kết quả.**
- Thử trên 101 CVE (C/C++ và Java). 41% số lần chạy tìm ra exploit mới sau khi bản vá đã chặn exploit ban đầu.
- Tỉ lệ đóng lỗ hổng trên bộ oracle độc lập tăng từ 78.1% lên 84.7% so với sửa một lượt bằng Claude Code.

## Từ khóa để tìm thêm tài liệu

SAST false positives, software composition analysis, SBOM, secret detection, infrastructure-as-code security, DevSecOps, CI/CD security gating, LLM vulnerability triage, taint analysis, source–sink–sanitizer, CWE, OWASP Top 10, security patch validation, alert fatigue.

## Tài liệu tham khảo (định dạng IEEE)

[1] R. Idan, T. Cohen Galor, A. Shabtai, and Y. Elovici, "An empirical security analysis of open-source software used in onboard satellite systems," arXiv:2609.15425, Sep. 2026.

[2] C. Wang, Z. Li, S. Dutta, and M. Naik, "QLCoder: A query synthesizer for static analysis of security vulnerabilities," in *Proc. Int. Conf. Learning Representations (ICLR)*, 2026, arXiv:2511.08462.

[3] F. Fleischer và cộng sự, "Contextualizing sink knowledge for Java vulnerability discovery," arXiv:2604.01645, 2026.

[4] M. Iranmanesh và cộng sự, "P2Patch: Exploit-guided vulnerability repair," arXiv:2610.20245, Oct. 2026.
