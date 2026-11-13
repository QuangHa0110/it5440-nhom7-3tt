# ADR 0003 — LLM nhận định bằng một lần gọi trên ngữ cảnh do chương trình trích, không dùng vòng lặp agent

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [architecture.md](../architecture.md) mục 2, 8; [ADR 0009](0009-langgraph-dieu-phoi-do-thi-nhan-dinh.md); proposal 6.3, 6.6, 11

## Bối cảnh

Hai dự án mã nguồn mở gần nhất chọn hai hướng. `sast-triage` cho agent tự đọc repo bằng `read_file` và `grep_repo` trong vòng lặp có trần. `sift-sast` dựng ngữ cảnh tất định bằng tree-sitter rồi mới gọi LLM. Proposal loại "agent đọc cả PR" khỏi phạm vi và coi ngữ cảnh luồng dữ liệu là phần phân tích chương trình chính của đề tài. Cách B và C phải khác nhau **chỉ** ở đầu vào thì so sánh mới có nghĩa.

## Quyết định

- **D1.** Mỗi cảnh báo, mỗi cách (B, C) có đúng một lần gọi LLM, cộng tối đa một lần gọi lại khi JSON sai schema.
- **D2.** LLM không có công cụ, không đọc thêm file, không chạy lệnh. Mọi mã nó thấy nằm trong prompt.
- **D3.** B và C dùng chung prompt và schema, chỉ khác phần dữ liệu ngữ cảnh.
- **D4.** Mỗi mục `evidence` trong đầu ra phải trỏ vào dòng nằm trong các `slices` đã gửi. Ngược lại nhận định thành `invalid`.
- **D5.** `likely_false` chỉ làm cảnh báo bị thu gọn. `unknown` và `invalid` luôn được giữ nguyên.

## Phương án khác

- **Agent tự đọc repo (kiểu sast-triage):** linh hoạt hơn nhưng B và C khó tách tác động, chi phí và thời gian khó đoán, và bề mặt tấn công qua mã trong PR lớn hơn.
- **Cho LLM xin thêm ngữ cảnh một vòng (kiểu Vulnhalla):** đỡ phần `missing` nhưng vẫn làm đầu vào của C phụ thuộc vào LLM.

## Hệ quả

- **Tốt hơn:** tái lập được, chi phí và thời gian có cận trên, hậu quả xấu nhất của chèn lệnh qua mã là một cảnh báo bị thu gọn.
- **Tệ hơn:** chất lượng phụ thuộc hoàn toàn vào bộ trích ngữ cảnh. Khi bộ trích bỏ sót, LLM chỉ có thể trả `unknown`.
- **Từ nay phải đúng:** `missing` được ghi đầy đủ ở mọi chỗ bộ trích không lần ra. Nếu số đo `missing` trên tập `dev` quá cao, mở ADR mới để xem xét lại quyết định này.
