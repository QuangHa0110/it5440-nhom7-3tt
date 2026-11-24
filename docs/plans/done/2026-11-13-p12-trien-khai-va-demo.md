# P12. Đóng gói, hướng dẫn cài đặt và bộ demo

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0012
- **Nhánh:** `trinq/deploy/docker-and-demo`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Người dùng cần chạy được và trình diễn được mà không phải đọc mã.

## Ngoài phạm vi

Không hạ tầng đám mây. Không tạo repo hay PR trên GitHub thật.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | Dockerfile và docker-compose, biến môi trường | `docker build` thành công | P11 |
| T2 | Manifest tạo GitHub App và hướng dẫn cài đặt, smee.io cho chạy cục bộ | Tài liệu đủ để làm theo từng bước | P11 |
| T3 | Bộ demo: mã nền, các PR mẫu (lỗ hổng thật, mã giống lỗi nhưng an toàn, thử chèn lệnh, không có gì), script dựng repo bằng `gh` | Script chạy chế độ `--dry-run` cục bộ ra đủ nhánh và commit | — |

## Cổng

```bash
make check
```

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `Dockerfile` (không chạy bằng root, có HEALTHCHECK) và `docker-compose.yml`; `docker build` thành công, container chạy thử: `/healthz` 200, chữ ký sai 401, `/stats` ẩn khi thiếu token. Manifest tạo App (`deploy/github-app-manifest.json`) và `scripts/github_app_manifest.py` (html, exchange, ghi bí mật ra tệp 0600 không in ra màn hình). Bộ demo: ứng dụng Java mẫu, 6 PR (SQL injection, truy vấn có tham số, chú thích cố lừa bot, secret, thay đổi vô hại, ép kiểu số nguyên) và `scripts/demo_repo.py` (--dry-run cục bộ hoặc đẩy lên GitHub bằng `gh`); test xác nhận từng kịch bản đúng như `pr.md` mô tả bằng Semgrep và bộ quét secret thật. Tài liệu `docs/github-app.md` và `docs/demo.md`.
- **Khác kế hoạch:** thêm luật Semgrep `java-sql-concat-flow` vì demo cho thấy luật cũ bỏ sót chuỗi SQL dựng ở biến rồi mới đưa vào `executeQuery`. Thêm `.gitleaks.toml` cho các giá trị giả của demo.
