# ADR 0007 — Tách thành ba job CI với ba mức quyền

- **Status:** proposed (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [architecture.md](../architecture.md) mục 6; proposal 6.6

## Bối cảnh

Mã trong PR là dữ liệu không đáng tin và có thể chứa chú thích nhằm lừa LLM. Một job vừa đọc mã, vừa gọi LLM, vừa giữ token ghi sẽ biến một lần chèn lệnh thành một đường ghi vào SCM.

## Quyết định

- **D1.** Job `triage` (`pr-triage run`) có credential **chỉ đọc** repo, đọc mã và gọi LLM, ghi `triage-result.json`. Không có token ghi.
- **D2.** Job `publish` (`pr-triage publish`) có credential **chỉ comment**, không checkout mã, không gọi LLM. Nó chỉ đọc kết quả đã được kiểm tra.
- **D3.** Job `feedback` và `replay` có credential chỉ đọc.
- **D4.** Mỗi job một container dùng một lần. Job `publish` chỉ chạy khi `triage` kết thúc, kể cả khi `triage` lỗi, để đăng thông báo "chưa quét xong".
- **D5.** Mọi job kết thúc thành công đối với PR, không tham gia điều kiện merge.

## Phương án khác

- **Một job duy nhất:** đơn giản hơn nhưng không có ranh giới quyền.

## Hệ quả

- **Tốt hơn:** chèn lệnh thành công cũng không chạm được token ghi.
- **Tệ hơn:** hai job và một artifact trung gian, cấu hình CI phức tạp hơn một chút.
- **Từ nay phải đúng:** `triage-result.json` có schema được kiểm tra ở `publish` trước khi dựng comment.
