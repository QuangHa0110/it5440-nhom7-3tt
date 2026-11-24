# ADR 0001 — Mô hình nhánh `main`/`dev`/nhánh cá nhân, release bằng tag và bump-my-version

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [git-workflow.md](../git-workflow.md)

## Bối cảnh

Nhóm 7 người cùng làm trong một repo public, trong khoảng một tháng, với nhiều mảng việc song song (quét, ngữ cảnh, LLM, bot, gán nhãn, thống kê, báo cáo). Các nhánh hiện có (`son-dev`, `kien-dev`, `docs/*`) đặt tên không theo quy ước chung. Proposal yêu cầu khóa cấu hình trước khi chạy tập `eval` và giữ kết quả tái lập được.

## Quyết định

- **D1.** `main` là release candidate, chỉ nhận merge từ `dev`.
- **D2.** `dev` là nhánh phát triển chung, chỉ nhận PR từ nhánh cá nhân.
- **D3.** Nhánh cá nhân đặt tên `{tên dev}/{slug}/{nội dung ngắn gọn}`, tách từ `dev`.
- **D4.** Release bằng tag `vX.Y.Z`. Phiên bản chỉ đổi bằng `bump-my-version`, nguồn duy nhất là `pyproject.toml`.
- **D5.** Tag không bao giờ bị xóa hay di chuyển, kể cả tag `eval-freeze-<n>`.
- **D6.** Hook `.claude/hooks/guard-git-safety.py` chặn force-push, xóa nhánh, `--no-verify` và sửa lịch sử trên `main`/`dev`.

## Phương án khác

- **Trunk-based chỉ có `main`:** đơn giản hơn nhưng `main` thiếu tầng đệm, mà nhóm cần một bản ổn định để báo cáo và nộp.
- **Git-flow đầy đủ (`release/*`, `hotfix/*`):** quá nặng cho nhóm nhỏ và vòng đời ngắn.

## Hệ quả

- **Tốt hơn:** có bản ổn định để báo cáo, lịch sử tái lập được qua tag, tên nhánh cho biết ai làm gì.
- **Tệ hơn:** thêm một lần PR từ `dev` sang `main` mỗi lần release.
- **Từ nay phải đúng:** mọi thay đổi vào `main` và `dev` đi qua PR có review và CI xanh. Branch protection cần được quản trị viên bật trên GitHub.
