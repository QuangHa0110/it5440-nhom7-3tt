# `docs/` — quy tắc tài liệu

`docs/README.md` là mục lục cho người đọc. File này là **hợp đồng** về việc từng loại tài liệu chứa gì và được sửa thế nào.

## Mỗi bề mặt dùng để làm gì

| Bề mặt | Chứa | Không chứa |
|---|---|---|
| `proposal-*.md` | Đề xuất đã được nhóm chốt, nguồn sự thật về phạm vi | Tiến độ, nhật ký |
| `adr/` | Mỗi file một quyết định: Bối cảnh / Quyết định / Phương án khác / Hệ quả | Cập nhật tiến độ |
| `plans/` | Mỗi kế hoạch một thư mục hoặc file có ngày, theo vòng đời `queued → active → done \| failed` | Quyết định (thuộc về ADR) |
| `devlog/` | Phát hiện bất ngờ, xung đột, vật cản gặp khi làm; mỗi mục một file có ngày | Báo cáo "đã làm xong" (thuộc về `plans/done/`) |
| `papers/`, `course/` | Chỉ link và ghi chú. PDF không vào git | PDF, tài liệu có bản quyền |

## Quy tắc

- **Quyết định đáng tranh luận → ADR. Việc nhiều bước → kế hoạch. Điều bất ngờ → devlog.** Ba loại không thay thế nhau.
- **ADR chỉ thêm, không sửa.** Muốn đổi thì viết ADR mới thay thế và thêm con trỏ vào ADR cũ. Số thứ tự liên tục, kiểm tra `ls adr | tail -1` trước khi lấy số.
- **Kế hoạch đã xong được chú thích, không viết lại.** Thêm ghi chú có ngày vào cuối. Khoảng cách giữa kế hoạch và thực tế là thông tin đáng giữ.
- **Kế hoạch chuyển bucket bằng `git mv`**, không sao chép. Mỗi task là một commit và có điều kiện hoàn thành quan sát được.
- **Khi đổi tên đường dẫn**, cập nhật tài liệu sống, giữ nguyên `plans/done`, `plans/failed` và `devlog` như đã lưu. Nếu để nguyên gây hiểu nhầm thì chú thích.
- **Số liệu không bắt nguồn từ tài liệu viết tay.** Số liệu tổng hợp lấy từ `results/` và được tạo lại bằng script trong `analysis/`.
- Repo public: trước khi thêm tài liệu, kiểm tra không có tên công ty Z, mã nguồn hay đường dẫn nội bộ.
