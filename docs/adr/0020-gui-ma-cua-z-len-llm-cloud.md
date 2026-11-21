# ADR 0020: Dùng LLM cloud cho mã của Z, kèm điều kiện về văn bản, nhà cung cấp và lượng dữ liệu gửi đi

- **Status:** accepted (2026-11-19)
- **Người quyết định:** hadvq
- **Liên quan:** thay thế dòng "Từ nay phải đúng" của [ADR 0008](0008-llm-gateway-openai-compat-va-bi-mat.md). Giữ nguyên D5 của ADR 0008 (`Redactor`, `allow_external`). Xem thêm [ADR 0013](0013-quet-secret-tich-hop.md) và [architecture.md](../architecture.md) mục 3

## Bối cảnh

- ADR 0008 coi mọi dịch vụ LLM bên ngoài là "LLM cloud" đối với dữ liệu của Z. ADR này chỉ cho dùng dịch vụ đó khi Z đồng ý bằng văn bản. Trước đây, việc cho phép hay không là câu hỏi còn mở ([architecture.md](../architecture.md) G4).
- Ngày 2026-11-19 nhóm nhận được trả lời: **Z cho phép gửi mã lên LLM cloud.**
- Mã nguồn đã có sẵn cơ chế bảo vệ:
  - `allow_external` mặc định tắt. Khi tắt, client từ chối gọi tới máy chủ ngoài danh sách cho phép (`llm/config.py`, `llm/client.py`).
  - Secret bị che hai lần: một lần khi chuẩn hóa cảnh báo, một lần ngay trước khi dựng prompt (`core/secrets.py`, `llm/engine.py`).
  - Mỗi cảnh báo chỉ gửi một gói ngữ cảnh nhỏ: đoạn mã quanh dòng bị báo (cách B), hoặc thêm lát luồng dữ liệu (cách C). Không gửi cả file hay cả repo ([ADR 0003](0003-llm-goi-mot-lan-khong-dung-agent.md)).
- Nếu phải chạy mô hình tại chỗ, Z cần có máy GPU, đồng thời rủi ro vượt trần 15 phút mỗi job sẽ tăng ([architecture.md](../architecture.md) mục 13).

## Quyết định

- **D1. Cách B và C chạy bằng mô hình cloud trên mã của Z.** Mô hình tại chỗ (Ollama hoặc vLLM) chỉ còn là phương án dự phòng. Client vẫn hỗ trợ nó mà không cần đổi mã.
- **D2. Phải có văn bản trước khi bật.** Chỉ đặt `PR_TRIAGE_LLM_ALLOW_EXTERNAL=1` trên hạ tầng của Z khi đã có văn bản đồng ý của Z (email hoặc biên bản). Văn bản phải nêu:
  - nhà cung cấp được phép;
  - những repo được gửi.

  Văn bản lưu ở phía Z, không đưa vào repo này vì repo là public.
- **D3. Nhà cung cấp và mô hình do Z chọn trong danh sách được phép.**
  - Nhà cung cấp phải cam kết trong điều khoản API rằng không dùng dữ liệu gửi qua API để huấn luyện mô hình.
  - Tên nhà cung cấp, địa chỉ cổng và khóa đặt trong biến môi trường của Z, không ghi vào repo (ADR 0008 D2, D3).
  - Mỗi lượt chạy vẫn ghi `model_id` vào `Verdict` và manifest.
- **D4. Gửi càng ít càng tốt.** Chỉ gửi gói ngữ cảnh của từng cảnh báo, sau khi đã che secret. Không gửi:
  - nội dung PR ngoài các đoạn mã đó;
  - lịch sử commit;
  - tên người;
  - đường dẫn tuyệt đối trên máy chạy.

  Phải có test bảo đảm prompt không chứa đường dẫn tuyệt đối hay chuỗi đã bị che.
- **D5. Có trần chi phí.** Đặt trần token mỗi cảnh báo và trần ngân sách mỗi ngày. Khi vượt trần, bot giữ nguyên cảnh báo gốc và không lọc (architecture.md nguyên tắc 3). Mỗi lượt chạy ghi số token và chi phí.
- **D6. Phạm vi RQ2 thay đổi.** Phép so sánh "mô hình tại chỗ với cloud" chuyển thành tùy chọn và chỉ làm nếu còn thời gian. RQ2 tập trung vào A, B, C trên cùng một mô hình cloud đã khóa trong manifest.

## Phương án khác

- **Chỉ dùng mô hình tại chỗ:** cách này không có dữ liệu nào rời khỏi Z. Nhưng Z phải có GPU, mô hình mở yếu hơn trong việc đọc mã, và có rủi ro vượt trần thời gian của job. Không cần thiết vì Z đã cho phép dùng cloud.
- **Chạy cả cloud lẫn tại chỗ cho mọi PR:** chi phí và công vận hành gấp đôi. Câu hỏi so sánh hai loại đã được giữ lại dưới dạng tùy chọn (D6).
- **Dùng dịch vụ lọc của hãng (Semgrep Assistant):** vẫn bị loại theo ADR 0005 D4, vì đó chính là thứ đề tài muốn đo một cách độc lập.

## Hệ quả

- **Tốt hơn:**
  - Không cần dựng máy chủ mô hình ở Z.
  - Có thể dùng mô hình mạnh.
  - Độ trễ ổn định hơn.
  - Có thể chạy đầu cuối B và C ngay khi có khóa.
- **Tệ hơn:**
  - Đoạn mã của Z rời khỏi hạ tầng của Z, dù đã được che và cắt nhỏ.
  - Chi phí theo token phát sinh hằng tháng, tỉ lệ với số cảnh báo. Với `p/default` và khoảng 300 PR mỗi tuần, con số này cần đo trước khi báo cho Z.
  - Phụ thuộc vào tính sẵn sàng của nhà cung cấp. Khi nhà cung cấp lỗi, bot rơi về cảnh báo gốc.
- **Từ nay phải đúng:**
  - Không bật `allow_external` trên dữ liệu của Z khi chưa có văn bản (D2).
  - Không tắt hay bỏ qua bước che secret trước khi gọi LLM.
  - Không ghi tên nhà cung cấp mà Z dùng, địa chỉ cổng hay khóa vào repo, log hay devlog.
  - Prompt và log thô có chứa mã của Z nằm lại trong Z, đúng như architecture.md mục 3.
  - Phiên Claude Code chạy không có người giám sát vẫn không đụng tới mã của Z ([plans/README.md](../plans/README.md) mục 6).
