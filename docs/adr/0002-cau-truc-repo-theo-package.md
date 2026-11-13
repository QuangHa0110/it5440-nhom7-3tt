# ADR 0002 — Cấu trúc repo theo package Python, tách mã, cấu hình, dữ liệu, báo cáo, tài liệu

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [ADR 0001](0001-mo-hinh-nhanh-va-release.md), proposal mục 6, 11, 13

## Bối cảnh

Khung ban đầu chia thư mục theo giai đoạn của bài (`pipeline/`, `analysis/`, `rules/`, `results/`, `paper/`, `slides/`), mỗi thư mục chỉ có README. Mã nằm trong script rời, không import, không test và khó chia việc. Prompt, schema và cấu hình `eval` chưa có chỗ. Tài liệu môn học lẫn với hồ sơ kỹ thuật. Khảo sát mã nguồn mở (chưa ghi vào devlog) cho thấy phần bot và cách A/B đã có công cụ tương tự, nên giá trị của nhóm nằm ở `normalize`, `context` và `evaluation`, cần là mã kiểm thử được.

## Quyết định

- **D1.** Một package `src/pr_triage/` với các gói con `scan`, `normalize`, `context`, `llm`, `bot`, `evaluation`, mỗi gói ứng với một phần việc ở proposal mục 13. `tests/` phản chiếu `src/`.
- **D2.** Cấu hình có phiên bản vào `configs/` (`semgrep`, `prompts`, `schemas`, `eval`). Tag `eval-freeze-<n>` khóa nội dung thư mục này.
- **D3.** `data/` chỉ chứa README và không bao giờ commit dữ liệu. Số liệu ẩn danh đã duyệt, bài báo và slide vào `reports/`.
- **D4.** Tài liệu dự án và môn học vào `docs/project/`. Chỉ có một `CLAUDE.md` ở gốc.
- **D5.** Ranh giới: `context`, `llm` và `evaluation` không import `bot`. Chưa dùng import-linter, kiểm tra bằng review cho đến khi cần.
- **D6.** mypy strict, ruff, pytest chạy ở CI. Hook `scripts/guard_public_repo.py` chặn dữ liệu nhạy cảm bằng danh sách cấm đặt ngoài repo.

## Phương án khác

- **Giữ cấu trúc theo giai đoạn:** không import được, khó test, người làm dễ viết trùng.
- **Nhiều package riêng:** quá nặng cho 7 người và một tháng.

## Hệ quả

- **Tốt hơn:** mỗi người một vùng mã, có CODEOWNERS; mã dùng chung và test được; cấu hình khóa được bằng tag.
- **Tệ hơn:** đổi đường dẫn tài liệu (`docs/*.md` sang `docs/project/`) làm hỏng liên kết ở các nhánh cũ.
- **Từ nay phải đúng:** README của gói con và `CODEOWNERS` được cập nhật khi chia lại phân công. Tên package `pr_triage` là tạm thời, đổi một lần bằng tìm và thay nếu nhóm chọn tên khác.
