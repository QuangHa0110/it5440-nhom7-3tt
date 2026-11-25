# ADR 0017 — Kiểm định mẫu 50 ca `eval` bằng một subagent AI độc lập thay cho người

- **Status:** accepted (2026-11-18). Thay phần "người dùng kiểm định" trong D2 của [ADR 0015](0015-danh-gia-ma-nguon-mo-nhan-ai.md); phần còn lại của ADR 0015 giữ nguyên.
- **Người quyết định:** người phụ trách đợt đánh giá (nhánh `feature/test-logs-minh`)
- **Liên quan:** thiết kế mục 6.5, runbook

## Bối cảnh

ADR 0015 dùng nhãn tham chiếu do Claude gán và dựa vào người dùng kiểm định độc lập 50 ca `eval` (khoảng 10–12 giờ) để chứng minh nhãn đúng. Người dùng yêu cầu giao việc kiểm định cho một subagent độc lập.

## Quyết định

- **D1.** Một subagent chạy mô hình **khác** người gán chính (Sonnet, người gán chính là Opus) gán nhãn mù 50 ca của `labels-eval-human-1.csv` bản sao `labels-eval-ai-subagent.csv`. Labeler alias: `ai-subagent` (không dùng `human-1`).
- **D2.** Subagent chỉ được đọc phiếu, ngữ cảnh mã (`audit-view.txt`), tiêu chí gán nhãn và mã nguồn tại commit; bị cấm đọc nhãn của người gán chính, DB, output nhận định B/C. Đây là ràng buộc bằng chỉ dẫn, không cưỡng chế được bằng kỹ thuật; subagent phải xác nhận đã tuân thủ.
- **D3.** Bất đồng được phân xử theo quy tắc của thiết kế 6.5 nhưng **không** có "người thắng": ca bất đồng được ghi `undetermined` trong nhãn cuối, trừ khi người dùng phân xử.
- **D4.** Báo cáo gọi kết quả là "nhãn tham chiếu của hai người gán AI (Opus/Sonnet), kappa = …, không có kiểm định bằng người". Phân tích độ nhạy `--only-labeled-by ai-subagent` vẫn được báo.

## Phương án khác

- **Người dùng kiểm định như ADR 0015:** mạnh nhất, nhưng người dùng không bố trí được thời gian.
- **Subagent cùng mô hình:** dễ lấy hơn, nhưng sai lệch tương quan cao hơn.

## Hệ quả

- **Tốt hơn:** có số đo đồng thuận giữa hai người gán độc lập mà không tốn giờ công.
- **Tệ hơn:** kappa đo sự nhất quán giữa hai mô hình, không đo độ đúng; cả hai có thể cùng sai một kiểu. Phép kiểm có đáp án duy nhất còn lại là hiệu chuẩn trên BenchmarkJava (B4, 29/30). Kết luận nghiên cứu yếu hơn so với ADR 0015.
- **Từ nay phải đúng:** không trình bày nhãn `ai-subagent` là nhãn người; nếu sau này người dùng kiểm định, thêm nhãn `human-1` và báo cả hai.
