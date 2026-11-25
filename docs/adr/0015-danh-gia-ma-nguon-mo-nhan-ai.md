# ADR 0015 — Đánh giá trên PR của repo Java mã nguồn mở, nhãn tham chiếu do AI gán và có người kiểm định mẫu

- **Status:** accepted (2026-11-18). D1 (nguồn cảnh báo, tách tập) được thay một phần bởi [ADR 0016](0016-quet-moc-lich-su-tach-tap-theo-repo.md); phần kiểm định người của D2 được thay bởi [ADR 0017](0017-kiem-dinh-bang-subagent-thay-nguoi.md)
- **Người quyết định:** người phụ trách đợt đánh giá (nhánh `feature/test-logs-minh`)
- **Liên quan:** thiết kế kịch bản đánh giá, kế hoạch, proposal mục 7.4, 8.3, 10; [ADR 0003](0003-llm-goi-mot-lan-khong-dung-agent.md)

## Bối cảnh

- Proposal giả định có repo, PR và người gán nhãn của công ty Z. Hạn quyết định 11/11 đã qua mà hồ sơ không có câu trả lời cho Phụ lục A. Proposal mục 8.3 đã dự liệu nhánh "Z rút lui → ứng dụng mã nguồn mở".
- Proposal mục 7.4 yêu cầu hai người gán nhãn độc lập trên `eval`, mục 10 ghi "AI không được dùng để tạo nhãn đáp án". Nhóm không bố trí được khoảng 65–100 giờ công gán nhãn.
- Model được cấu hình trong `.env` là model cloud, không có model chạy tại chỗ.
- Bộ trích ngữ cảnh C chỉ hỗ trợ Java, danh mục `configs/context/java.yml` có sink cho CWE-89, 78, 79, 22, 90, 643.

## Quyết định

- **D1.** Tạm thời không dùng dữ liệu công ty Z. Dữ liệu chính là PR đã merge của 1–3 repo Java mã nguồn mở. OWASP BenchmarkJava là phép kiểm chéo có đáp án, Vul4J cho RQ4. Báo cáo không gọi các repo này là "công ty Z".
- **D2.** Claude gán nhãn toàn bộ (`ai-claude`) theo Phụ lục B, mù với nhận định của model được đánh giá: mỗi tập được gán nhãn xong trước khi chạy B/C trên tập đó. Người dùng kiểm định độc lập 50 ca `eval` lấy mẫu phân tầng (`human-1`); khi bất đồng, nhãn người là nhãn cuối.
- **D3.** Trước khi gán D1, Claude được hiệu chuẩn trên 30 ca BenchmarkJava so với đáp án có sẵn. Kappa giữa Claude và người dưới 0,6 thì sửa tiêu chí và gán lại; lần hai vẫn dưới 0,6 thì chỉ báo kết quả trên phần có nhãn người.
- **D4.** Bỏ H2c (model tại chỗ so với cloud).
- **D5.** Phạm vi CWE của đánh giá là 6 CWE nhóm injection có trong danh mục ngữ cảnh.

## Phương án khác

- **Chờ công ty Z:** đúng đề cương nhất nhưng không có ngày chắc chắn.
- **Chỉ dùng benchmark có đáp án:** không cần gán nhãn, nhưng tỉ lệ cảnh báo sai nền cao và mô hình có thể đã thuộc dữ liệu, đi ngược luận điểm chính của đề tài.
- **AI gán nhãn không có người kiểm định:** không có gì chứng minh nhãn đúng.
- **Nhóm gán nhãn theo proposal:** mạnh nhất nhưng không bố trí được thời gian.

## Hệ quả

- **Tốt hơn:** làm được ngay, tái lập được vì dữ liệu công khai, vẫn có đối chứng bằng người và bằng đáp án có sẵn.
- **Tệ hơn:** kết quả không phải số liệu doanh nghiệp và không dùng được cho tiêu chí mức A cần thư xác nhận. Nhãn tham chiếu do AI gán có thể cùng sai một kiểu với model được đánh giá, làm số đo đẹp giả tạo. Mô hình có thể đã thấy mã nguồn mở khi huấn luyện.
- **Từ nay phải đúng:** báo cáo ghi rõ "nhãn tham chiếu AI, kiểm định người trên n = 50" và kappa; không trình bày nhãn AI như nhãn người; luôn gán nhãn trước khi chạy B/C trên cùng tập; nếu sau này có dữ liệu Z, viết ADR mới thay thế D1.

## Ghi chú 2026-11-24

- Số 0015–0017 được nhóm giữ chỗ cho đợt này (xem ADR 0019, mục "Đánh số lại"); ba ADR được đưa vào repo nguyên số.
- Đây là **đợt 1** (cấu hình khóa bằng tag `eval-freeze-1`: 3 luật tự viết cộng 29 luật registry, trước ADR 0019). Đợt 2 theo `docs/huong-dan-chon-repo-va-pr.md`: quét bằng `p/default`, dữ liệu mức PR, nhãn do người gán, không dùng AI. `CLAUDE.md` và hướng dẫn đó giữ nguyên quy tắc "không dùng AI gán nhãn"; phần nhãn AI của ADR này và ADR 0017 chỉ áp dụng cho đợt 1.
- Số liệu đợt 1 không gộp với đợt 2 (luật, đơn vị phân tích và người gán nhãn khác nhau).
