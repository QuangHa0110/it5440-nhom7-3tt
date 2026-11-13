# `docs/devlog/` — nhật ký kỹ thuật

Nơi ghi **phát hiện**, không ghi việc đã xong: xung đột, vật cản, giả định sai gặp khi làm mà **có thể buộc đổi proposal hoặc phương pháp**. Việc đã xong thuộc về `plans/done/`.

| Bản ghi | Trả lời câu hỏi | Sửa được không |
|---|---|---|
| `adr/` | Ta đã quyết gì và vì sao? | Chỉ thêm |
| `plans/` | Ta định làm gì, làm xong chưa? | Chú thích, không viết lại |
| `devlog/` | Ta gặp điều gì bất ngờ? | Không sửa sau khi lưu |
| [`debt-ledger.md`](debt-ledger.md) | Còn nợ gì? | Thêm khi phát sinh, đóng khi xong |

## Quy ước

- Mỗi mục một file: `YYYY-MM-DD-<slug>.md`. Mở đầu gồm: **Phát hiện**, **Vì sao quan trọng**, **Đề xuất điều chỉnh**.
- Mức độ: 🔴 có thể đổi một kết luận hoặc RQ, 🟡 phải thay thế khi triển khai nhưng kết luận giữ nguyên, 🟢 ghi chú, ⊘ hoãn.
- Số liệu không nằm ở đây. Chúng nằm trong `reports/results/` và được tạo bởi script trong `src/pr_triage/evaluation/`.
- Repo public: không ghi tên Z, mã nguồn hay đường dẫn nội bộ.

## Mục lục (mới nhất ở trên)

- [2026-11-13 Semgrep CE không nối taint xuyên hàm](2026-11-13-semgrep-ce-khong-noi-taint-xuyen-ham.md) 🟢
- [2026-11-13 Ba tên mô hình trên cổng LLM cho kết quả giống nhau](2026-11-13-cong-llm-ba-ten-mo-hinh-cho-ket-qua-giong-nhau.md) 🟡
