# ADR 0010 — Thu phản hồi theo từng cảnh báo bằng lệnh trả lời `fp` và `tp`

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq (đã đồng ý ý tưởng ngày 2026-11-13)
- **Liên quan:** [architecture.md](../architecture.md) mục 10.1; proposal 6.5, 7.6

## Bối cảnh

Proposal đo phản hồi bằng phản ứng 👍/👎 trên comment. Một comment chứa nhiều cảnh báo nên một phản ứng không cho biết nó nói về cảnh báo nào, trong khi số đo RQ3 (tỉ lệ cảnh báo sai hiệu dụng) tính theo từng cảnh báo hiển thị.

## Quyết định

- **D1.** Mỗi cảnh báo trong comment có một mã ngắn `finding_id` (6 ký tự hex đầu, kèm kiểm tra không trùng trong PR).
- **D2.** Lập trình viên phản hồi bằng cách trả lời comment với `fp <mã>` hoặc `tp <mã>`. Có thể kèm lý do ngắn sau mã.
- **D3.** Phản ứng trên comment tổng được ghi như một kênh riêng, dùng cho câu hỏi "comment có ích không", không quy về từng cảnh báo.
- **D4.** Cảnh báo mức High trở lên được phép có comment theo dòng riêng, mỗi comment có phản ứng riêng. Đây là mục "nên có" của proposal, làm sau.
- **D5.** Người thao tác được ẩn danh bằng băm có muối, muối nằm trong Z. Phản hồi không dùng để đánh giá cá nhân.
- **D6.** Phản hồi là dữ liệu hành vi, không phải nhãn kỹ thuật. Nó không bao giờ ghi vào bảng `Label`.

## Phương án khác

- **Chỉ dùng phản ứng:** đơn giản nhưng không phân biệt được cảnh báo.
- **Nút bấm hoặc biểu mẫu ngoài SCM:** phải xin Z thêm công cụ, đi ngược mục tiêu ít can thiệp.

## Hệ quả

- **Tốt hơn:** đo được phản hồi theo từng cảnh báo.
- **Tệ hơn:** lập trình viên phải gõ lệnh, nên tỉ lệ phản hồi có thể thấp. Đây là kết quả của RQ3, được báo cáo như vậy.
- **Từ nay phải đúng:** cú pháp lệnh được ghi ở đầu comment của bot. `ScmPort` phải đọc được các câu trả lời trên comment. Nếu SCM của Z không cho đọc, chỉ còn kênh phản ứng.
