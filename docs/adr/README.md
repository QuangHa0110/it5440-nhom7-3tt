# `docs/adr/` — Architecture Decision Records

Mỗi file là một quyết định đáng tranh luận. Tên file: `NNNN-tieu-de-viet-khong-dau.md`, số thứ tự liên tục, không bỏ số.

- **Chỉ thêm, không sửa.** Muốn đổi quyết định thì viết ADR mới, đặt `Status: supersedes NNNN` và thêm một dòng con trỏ vào ADR cũ.
- Bắt đầu từ [_template.md](_template.md). Kiểm tra `ls | tail -1` trước khi lấy số mới.

| ADR | Quyết định | Trạng thái |
|---|---|---|
| [0001](0001-mo-hinh-nhanh-va-release.md) | Mô hình nhánh `main`/`dev`/nhánh cá nhân, release bằng tag và bump-my-version | accepted |
| [0002](0002-cau-truc-repo-theo-package.md) | Cấu trúc repo theo package Python, tách mã, cấu hình, dữ liệu, báo cáo, tài liệu | proposed |
