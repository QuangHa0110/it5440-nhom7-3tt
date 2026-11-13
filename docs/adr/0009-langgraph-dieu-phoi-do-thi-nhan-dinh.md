# ADR 0009 — LangGraph điều phối đồ thị nhận định cho từng cảnh báo, không dùng làm agent tự do

- **Status:** proposed (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [ADR 0003](0003-llm-goi-mot-lan-khong-dung-agent.md), [architecture.md](../architecture.md) mục 8.2, sơ đồ 5

## Bối cảnh

Yêu cầu của người dùng: dùng LangGraph cho phần agent nếu chưa có mã nguồn mở làm sẵn. Mã nguồn mở đã có (`sast-triage`, `sift-sast`) nhưng không fork được vì lý do ở ADR 0005. ADR 0003 quyết định không có vòng lặp agent tự do. Hai điều này không mâu thuẫn nếu LangGraph được dùng như **bộ điều phối trạng thái**, không phải bộ ra quyết định.

Sơ đồ 5 là một đồ thị hữu hạn: tra cache, kiểm tra ngân sách, che secret, dựng prompt, gọi mô hình, kiểm tra, gọi lại một lần, lưu. Mỗi nút tất định ngoại trừ nút gọi mô hình.

## Quyết định

- **D1.** Cài đặt `TriageEngine` bằng một `StateGraph` của LangGraph với trạng thái kiểu `TypedDict`: `finding`, `bundle`, `variant`, `redacted`, `messages`, `raw`, `verdict`, `attempts`, `error`.
- **D2.** Các nút: `lookup_cache`, `check_budget`, `redact`, `build_prompt`, `call_model`, `validate`, `store`. Cạnh có điều kiện: cache trúng thì tới `store`, hết ngân sách thì tới `store` với `unknown`, `validate` lỗi và `attempts < 2` thì quay lại `call_model`.
- **D3.** **Không có công cụ, không có nút tự quyết định gọi nút khác.** Đồ thị là DAG cộng đúng một cạnh lùi có trần. Test khẳng định số lần `call_model` không vượt 2.
- **D4.** Nút `call_model` gọi `OpenAICompatClient` của ADR 0008, không dùng lớp mô hình của LangChain. Chỉ phụ thuộc `langgraph`, không phụ thuộc `langchain`.
- **D5.** `LlmPort` vẫn là cổng. Pipeline không biết LangGraph tồn tại. Có một bộ hiện thực `PlainTriageEngine` bằng hàm Python thuần dùng cho test và làm mốc đối chiếu hành vi.
- **D6.** Khi đồ thị cần mở rộng ngoài D3 (ví dụ cho phép xin thêm ngữ cảnh), phải có ADR mới thay thế ADR 0003.

## Phương án khác

- **Hàm Python thuần, không LangGraph:** ít phụ thuộc, ngắn hơn. Đồ thị này đủ nhỏ để viết thuần. Đây là phương án thay thế đáng cân nhắc nếu LangGraph gây rắc rối cài đặt trong môi trường Z.
- **LangGraph làm agent ReAct với công cụ đọc file:** đúng nghĩa "agent" nhưng đi ngược ADR 0003.

## Hệ quả

- **Tốt hơn:** trạng thái, thử lại và đường rẽ nhìn thấy được và test được theo từng nút. Dễ mở rộng nếu nhóm sau này muốn thử một biến thể agent làm cách D.
- **Tệ hơn:** thêm một phụ thuộc lớn cho một đồ thị bảy nút. Phải khóa phiên bản.
- **Từ nay phải đúng:** hành vi của `TriageEngine` và `PlainTriageEngine` trùng nhau trên cùng đầu vào. Nếu LangGraph không cài được ở Z, `PlainTriageEngine` thay thế mà không đổi kết quả.
