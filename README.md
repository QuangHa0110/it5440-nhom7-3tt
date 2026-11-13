# IT5440 – Nhóm 7 – Đề tài 3TT

**Phân tích chương trình hướng bảo mật (Chương 11) – Hướng đánh giá triển khai thực tế**

Học phần IT5440 Nguyên lý và kỹ thuật phân tích chương trình, học kỳ 2026.1, ĐHBK Hà Nội.

Hướng TT: áp dụng các kỹ thuật phân tích chương trình hướng bảo mật vào hoạt động phát triển phần mềm của một doanh nghiệp (gọi là **công ty Z**), đánh giá hiệu quả triển khai và viết báo cáo đủ điều kiện đăng arXiv. Nội dung triển khai cụ thể sẽ do nhóm thống nhất.

## Tài liệu

| File | Nội dung |
|---|---|
| [docs/huong-dan-tieu-luan.md](docs/huong-dan-tieu-luan.md) | Tóm tắt yêu cầu, cách chấm điểm, lịch báo cáo và quy cách trình bày |
| [docs/tom-tat-bai-bao.md](docs/tom-tat-bai-bao.md) | Tóm tắt 4 bài báo giảng viên giao và cách dùng trong đề tài |
| [docs/papers/README.md](docs/papers/README.md) | Link tải 4 bài báo (PDF không lưu trên repo) |
| [docs/proposal-llm-loc-canh-bao-pr.md](docs/proposal-llm-loc-canh-bao-pr.md) | Proposal đề tài: LLM lọc cảnh báo bảo mật trên PR |
| [docs/git-workflow.md](docs/git-workflow.md) | Quy trình nhánh, PR, release |
| [docs/adr/](docs/adr/), [docs/plans/](docs/plans/), [docs/devlog/](docs/devlog/) | Quyết định, kế hoạch, nhật ký kỹ thuật |
| [CLAUDE.md](CLAUDE.md) | Ngữ cảnh cho Claude Code |

## Cấu trúc thư mục

```
docs/        Tài liệu, kế hoạch, tóm tắt bài báo
pipeline/    Script và cấu hình chạy các công cụ quét, file CI
rules/       Luật Semgrep/CodeQL tùy biến (kể cả luật do LLM sinh)
analysis/    Script hợp nhất, khử trùng lặp, gán nhãn, thống kê
results/     Số liệu tổng hợp ĐÃ ẨN DANH (kết quả thô nằm ngoài git)
paper/       Bài báo (LaTeX) và báo cáo đầy đủ
slides/      Slide các lần báo cáo
```

## Quy tắc của repo

Repo đang ở chế độ **public**:

- **Không commit** tên công ty Z, tên dự án nội bộ, đoạn mã nguồn, đường dẫn nội bộ hay kết quả quét thô. Kết quả thô để trong `results/raw/` hoặc `results/company/`, hai thư mục này đã nằm trong `.gitignore`.
- **Không bao giờ commit secret.** Secret tìm thấy khi quét chỉ báo riêng cho công ty để thu hồi.
- Không commit PDF bài báo, tài liệu của giảng viên hay danh sách học viên.
- Nhánh: `main` (release candidate, tag `vX.Y.Z`), `dev` (phát triển chung), nhánh cá nhân `{tên dev}/{slug}/{nội dung}` mở PR vào `dev`. Chi tiết: [docs/git-workflow.md](docs/git-workflow.md).
- Sau khi clone: `make setup` (môi trường uv và pre-commit). Trước khi mở PR: `make check`.

## Mốc thời gian

| Thời gian | Mốc |
|---|---|
| Tuần 4–5/11/2026 | Chốt nhóm và đề tài |
| Tuần 18–19/11/2026 | Báo cáo lần 1: xong ít nhất 2/4 nội dung |
| Tuần 25–26/11/2026 | Báo cáo lần 2: xong ít nhất 3/4 nội dung |
| Tháng 12/2026 | Hoàn thiện, nộp sản phẩm và bảo vệ |
