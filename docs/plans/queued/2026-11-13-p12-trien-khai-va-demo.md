# P12. Đóng gói, hướng dẫn cài đặt và bộ demo

- **Status:** queued
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0012
- **Nhánh:** `trinq/deploy/docker-and-demo`
- **Bắt đầu / Kết thúc:** — / —

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
