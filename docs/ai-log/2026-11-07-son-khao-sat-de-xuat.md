# 07/11/2026 – Sơn – Khảo sát tài liệu và đề xuất

| | |
|---|---|
| Công cụ | Claude Code (Claude Opus 5.5), chế độ deep research với 4 agent tìm kiếm chạy song song, cộng 1 agent tổng hợp |
| Sản phẩm | `docs/khao-sat/`, `docs/de-xuat-son.md` |
| Dữ liệu đưa vào AI | Hướng dẫn tiểu luận và đề cương của thầy, 4 bài báo đề tài 3, các tài liệu đang có trên repo. Không có dữ liệu công ty, không có secret |

## Yêu cầu chính

> Đọc task, tìm đề xuất phù hợp với bài tập lớn: đủ dễ để làm được, nhưng đủ tốt và có đóng góp để đạt điểm cao. Deep research trước rồi mới đề xuất. Không đi quá sâu vì nhóm chưa chốt ý tưởng.

## Bốn hướng tìm kiếm giao cho agent

1. LLM lọc cảnh báo SAST và review bảo mật pull request bằng LLM/agent (2023–2026). Mục tiêu: xem hướng A/B/C/D trong bản nháp đã đông đến mức nào.
2. Phát hiện secret và SCA có reachability/VEX.
3. Sinh luật Semgrep/CodeQL bằng LLM, kiểm thử hồi quy bảo mật, kiểm chứng bản vá, lỗ hổng tái phát.
4. Cách các bài công nghiệp đo hiệu quả triển khai phân tích tĩnh; chuẩn ACM SIGSOFT cho case study.

## Người kiểm tra lại những gì

- Đối chiếu với PDF gốc: 22,2% cảnh báo sai (KTC 95%: 17,6–27,6%) trong bài vệ tinh; kết quả 41 so với 8 lỗ hổng của GONDAR so với Jazzer.
- Mở trang arXiv của SEVRA-BENCH, SecPRBench và "Sifting the Noise" để kiểm tra phạm vi thật của từng bài. Đã ghi kết quả ở đầu `docs/khao-sat/tong-quan-tai-lieu.md`.
- **Chưa kiểm tra:** các tài liệu có đánh dấu "Ghi chú: …" trong file khảo sát. Phải đọc bản gốc trước khi đưa vào báo cáo.

## Phần do người quyết định

Việc chọn P1 làm đề xuất chính, các ngưỡng, phạm vi và kế hoạch đều là đề xuất để cả nhóm thảo luận, chưa phải quyết định cuối cùng.
