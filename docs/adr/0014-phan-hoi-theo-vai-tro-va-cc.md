# ADR 0014 — Phản hồi theo vai trò người gõ, chính sách CC người liên quan, làm sạch nội dung do mô hình sinh

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [ADR 0010](0010-phan-hoi-theo-tung-canh-bao.md), [ADR 0003](0003-llm-goi-mot-lan-khong-dung-agent.md)

## Bối cảnh

Với PR từ bên ngoài, phản hồi `fp` do chính tác giả gõ có xung đột lợi ích. Người dùng cũng muốn bot báo cho người liên quan. Nội dung giải thích do mô hình sinh từ mã của người gửi nên có thể chứa `@mention` hoặc HTML nhằm gây nhiễu.

## Quyết định

- **D1.** Mỗi phản hồi ghi vai trò: `author` (tác giả PR), `reviewer` (OWNER, MEMBER, COLLABORATOR), `other`.
- **D2.** Cấu hình `feedback.trusted_roles` quyết định phản hồi `fp` của vai trò nào làm cảnh báo thành "bị đánh dấu sai". Mặc định `[author, reviewer]`. Kịch bản outsource nên đặt `[reviewer]`. Phản hồi của vai trò không tin cậy vẫn được ghi nhưng chỉ tính là "có phản hồi".
- **D3.** CC cấu hình bằng `mentions.mode`: `none`, `author`, `codeowners`, `list`, kết hợp được. Chỉ CC khi có cảnh báo từ mức `mentions.min_severity`. Mặc định `none`.
- **D4.** Mọi nội dung do mô hình hoặc do mã của PR sinh ra (giải thích, đường dẫn, thông điệp) được làm sạch trước khi đưa vào comment: vô hiệu hóa `@`, thoát HTML, cắt độ dài.
- **D5.** Danh sách CC chỉ gồm người từ tác giả PR, `CODEOWNERS` của nhánh đích hoặc danh sách cấu hình. Không bao giờ lấy từ nội dung do mô hình sinh.

## Hệ quả

- **Tốt hơn:** phản hồi đáng tin hơn, không bị lợi dụng để gửi thông báo.
- **Tệ hơn:** thêm một tham số cấu hình cần giải thích cho khách.
- **Từ nay phải đúng:** không đưa chuỗi do mô hình sinh vào comment mà không qua bộ làm sạch.
