# ADR 0019 — Quét bằng bộ luật Semgrep `p/default`, tải về trong hạ tầng chạy bot và khóa bằng mã băm, không commit luật

- **Status:** accepted (2026-11-19)
- **Người quyết định:** hadvq
- **Liên quan:** [ADR 0005](0005-dung-lai-ma-nguon-mo.md) (hoãn D1 phần FindSecBugs), [ADR 0011](0011-dau-van-tay-va-so-head-base.md), kế hoạch [P15](../plans/done/2026-11-19-p15-semgrep-bo-luat-co-san.md), nợ TD-2
- **Đánh số lại 2026-11-21:** trước đây là ADR 0015. Các số 0015 đến 0017 đã được đợt đánh giá nguồn mở giữ chỗ ngoài repo, nên ADR này đổi sang 0019 trước khi đưa vào `dev`.

## Bối cảnh

- Bot đang quét bằng 3 luật nhóm tự viết, chỉ phủ SQL injection (`configs/semgrep/java-injection.yml`). Số liệu đo trên bộ luật này không cho biết một công ty thật sẽ gặp bao nhiêu cảnh báo, bao nhiêu là sai.
- Công ty Z chưa có công cụ phân tích tĩnh nào trong CI (xác nhận 2026-11-18). Vì vậy cách A ("chỉ công cụ quét") là một lựa chọn thật của Z: chỉ cài Semgrep. Bộ luật phải là bộ Z sẽ cài nếu tự làm.
- Bộ luật trong registry của Semgrep dùng **Semgrep Rules License v1.0**: được dùng cho mục đích nội bộ của doanh nghiệp, **không được phân phối lại** hay cung cấp như dịch vụ. Repo này là public.
- `manifest_hash` (`pipeline/build.py`) băm **nội dung** file luật. Nếu truyền tên registry (`p/default`) thì chỉ băm chuỗi tên, trong khi nội dung trên registry thay đổi theo thời gian. Khi đó tag khóa cấu hình eval không còn ý nghĩa.
- So sánh ngày 2026-11-18, Semgrep 1.186.0, trên 7 nhánh của repo demo (chi tiết ở P15, mục Hiện trạng):

| Bộ | Luật Java | Nhận xét |
|---|---|---|
| `p/java` | 60 (độ tin cậy cao và trung bình) | Không báo PR #6 (nối chuỗi số nguyên), nên bộ lọc gần như không có việc |
| `p/owasp-top-ten` | 60, trùng hệt `p/java` | Thêm Java không được gì |
| `p/default` | 118, chứa trọn `p/java`, thêm 45 luật độ tin cậy thấp | Bộ mặc định Semgrep khuyến nghị cho CI, phủ mọi ngôn ngữ |
| `p/security-audit` | 52 | Semgrep ghi là bộ audit, nhiều tiếng ồn |
| `p/findsecbugs` | 141, 92 luật không ghi độ tin cậy | Nhiều tiếng ồn |

## Quyết định

- **D1.** Công cụ quét chính là Semgrep CE với bộ **`p/default`**, đủ mọi ngôn ngữ. Không chọn bộ nhiều tiếng ồn, vì tỉ lệ báo sai nền cao giả tạo sẽ làm bộ lọc LLM trông tốt hơn thật. Không chọn `p/java`, vì nó sạch hơn thứ một công ty thường cài.
- **D2.** File luật **không bao giờ vào repo**. `scripts/fetch_semgrep_rules.py` tải luật trong hạ tầng nơi bot chạy (máy dev, image Jenkins của Z) vào `data/rules/` (đã có trong `.gitignore`). Repo chỉ giữ `configs/semgrep/rulesets.lock`, gồm tên bộ, URL, ngày tải, sha256 và số luật.
- **D3.** Bot chỉ chạy từ file đã tải. Nội dung file lệch mã băm trong lock thì dừng với lỗi rõ ràng. Đổi bộ luật là một commit sửa lock, và phải làm trước khi gắn tag khóa eval.
- **D4.** Test vẫn dùng `java-injection.yml`, vì test cần chạy không có mạng và có kết quả cố định. File đó không còn là luật mặc định khi chạy thật.
- **D5.** Hoãn SpotBugs với FindSecBugs (ADR 0005 D1). Một công cụ quét đủ cho RQ1 và RQ2, còn công cụ thứ hai làm phép gộp và gán nhãn phức tạp thêm. Có thể thêm sau như một bộ chuyển đổi SARIF.
- **D6.** So sánh B với C chỉ tính trên cảnh báo Java, vì bộ trích luồng dữ liệu của C hiện chỉ hỗ trợ Java. Với CWE không có luồng dữ liệu (như mật mã yếu), C ghi rõ là không áp dụng, không đoán.

## Phương án khác

- **Giữ luật tự viết:** phạm vi hẹp, không đại diện cho thứ Z sẽ cài. Bị phản biện ngay ở câu "đo có đúng thực tế không".
- **Gọi thẳng `--config p/default` lúc quét:** đơn giản, nhưng nội dung trôi theo registry nên không khóa được cấu hình. Mỗi lần quét cũng cần mạng.
- **Commit bản sao luật vào repo:** khóa dễ nhất, nhưng vi phạm điều khoản không phân phối lại.
- **Opengrep và bộ luật của nó:** engine dùng LGPL-2.1. Chưa kiểm tra được giấy phép của bộ luật. Giữ làm phương án dự phòng nếu điều khoản của Semgrep cản việc chạy ở Z.
- **SonarQube:** Z không có. Bản miễn phí không phân tích PR và không có taint.

## Hệ quả

- **Tốt hơn:** cách A phản ánh đúng lựa chọn "chỉ cài Semgrep" của Z. Phạm vi phủ đủ các CWE phổ biến, và cấu hình eval khóa được bằng mã băm.
- **Tệ hơn:** máy chạy bot cần ra internet một lần để tải luật. Quét chậm hơn (một nhánh demo mất khoảng 23 giây thay vì vài giây). Comment có thể dài hơn. Một số cảnh báo không có luồng dữ liệu, nên cách C không giúp được gì so với B ở các cảnh báo đó.
- **Từ nay phải đúng:**
  - Không commit file nào dưới `data/`, kể cả luật.
  - Mỗi lượt chạy ghi sha256 của bộ luật vào manifest.
  - Mọi báo cáo số liệu nêu tên bộ luật và ngày tải.
  - Trước khi chạy trên mã của Z, đọc lại điều khoản Semgrep Rules License. Nếu cần, để Z tự tải và chạy luật trong hạ tầng của Z.
