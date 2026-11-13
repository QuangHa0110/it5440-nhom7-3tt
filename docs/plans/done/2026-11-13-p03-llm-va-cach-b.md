# P03. Máy nhận định bằng LLM và cách B

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Đóng:** cách B chạy được trên cổng LLM thật
- **Quyết định cho phép:** ADR 0003, 0008, 0009
- **Nhánh:** `trinq/llm/triage-engine`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Đây là nơi hệ thống gọi mô hình. Dịch vụ LLM dùng khi phát triển là thông tin nội bộ của nhóm, không ghi trong repo.

## Ngoài phạm vi

Ngữ cảnh luồng dữ liệu (P04). Cache dùng chung giữa các máy. Tinh chỉnh mô hình.

## Hiện trạng đã kiểm chứng

2026-11-13: dịch vụ LLM của nhóm trả JSON hợp lệ cho một lời nhắc đơn giản. Chưa thử với prompt dài, chưa đo giới hạn tốc độ.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `OpenAICompatClient` bằng `httpx`, cấu hình từ biến môi trường, che khóa trong log, kiểm tra `finish_reason` | Test với máy chủ giả; test khẳng định khóa không có trong log | P01 |
| T2 | `Redactor` che secret | Test: chuỗi giống khóa và mật khẩu trong mã mẫu bị che, mã còn lại giữ nguyên | P01 |
| T3 | JSON schema của `Verdict` và `VerdictValidator` kiểm tra schema và bằng chứng nằm trong `slices` | Test: bằng chứng ngoài ngữ cảnh làm nhãn thành `invalid` | P01 |
| T4 | `PromptBuilder` (mã nằm trong khối dữ liệu có phân cách) kèm bộ test chèn lệnh | Test: chú thích "ignore previous instructions" trong mã không đổi cấu trúc prompt | T3 |
| T5 | `BudgetGuard` và `VerdictCache` (khóa theo ADR 0003, 0008) | Test: lần gọi thứ hai cùng khóa không gọi client, hết ngân sách trả `unknown` | T1 |
| T6 | `PlainTriageEngine` bằng hàm Python thuần | Test đầy đủ trên máy chủ giả: trúng cache, hết ngân sách, JSON sai rồi đúng, JSON sai hai lần | T1 đến T5 |
| T7 | `TriageEngine` bằng LangGraph cùng hành vi (ADR 0009) | Cùng bộ test T6 qua cho cả hai, test số lần gọi mô hình không vượt 2 | T6 |
| T8 | `SnippetProvider` (cách B): hàm bao quanh cộng 10 dòng trước sau | Test trên mã Java mẫu | P02 |
| T9 | Thử trực tiếp trên cổng thật: 20 cảnh báo của một repo công khai, cả ba mô hình | Bảng tỉ lệ JSON hợp lệ, thời gian, token ghi vào devlog | T7, T8 |

## Cổng

```bash
make check && PR_TRIAGE_LLM_API_KEY=... uv run pytest -m integration tests/llm
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Mô hình bọc JSON trong văn bản hay khối mã | `validate` lỗi nhiều | Bóc khối mã trước khi kiểm tra, vẫn đếm là một lần gọi |
| LangGraph khó cài hoặc đổi API | `uv sync` lỗi hoặc test T7 lỗi vặt | Khóa phiên bản, dùng `PlainTriageEngine` làm mặc định, báo trong devlog |
| Cổng LLM giới hạn tốc độ | Lỗi 429 | Thử lại có lùi, hạ số cảnh báo chạy song song |

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `make check` qua với 78 test, gồm 2 test thật trên cổng LLM (cả hai máy nhận định). Có `OpenAICompatClient`, `Redactor`, `VerdictValidator`, `PromptBuilder`, `BudgetGuard`, `VerdictCache`, `PlainTriageEngine` và `TriageEngine` (LangGraph) cho kết quả trùng nhau, `SnippetProvider`. Thử 30 cảnh báo thật: JSON hợp lệ 30/30 ở cả ba mô hình.
- **Khác kế hoạch:** thêm biến `PR_TRIAGE_LLM_ALLOW_EXTERNAL` và `PR_TRIAGE_LLM_JSON_MODE`. Mở rộng `SymbolIndex` (nút phương thức, tìm lời gọi) làm sớm cho P04. Luật Semgrep mở rộng nguồn và sink để chạy trên Benchmark.
