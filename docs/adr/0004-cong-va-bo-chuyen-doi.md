# ADR 0004 — Kiến trúc cổng và bộ chuyển đổi, với ba gói nền `core`, `store`, `pipeline`

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [ADR 0002](0002-cau-truc-repo-theo-package.md), [architecture.md](../architecture.md) mục 5

## Bối cảnh

Công ty Z chưa trả lời Phụ lục A, nên CI, SCM, ngôn ngữ, công cụ quét và mô hình đều có thể đổi. Khung repo ban đầu có sáu gói nhưng thiếu chỗ cho mô hình miền, lưu trữ và điều phối.

## Quyết định

- **D1.** Thêm ba gói `core` (mô hình miền và cổng), `store` (SQLite và blob) và `pipeline` (điều phối). ADR 0002 được bổ sung, không bị thay thế.
- **D2.** Năm cổng định nghĩa bằng `typing.Protocol` trong `core`: `ScannerPort`, `ContextPort`, `LlmPort`, `ScmPort`, `StorePort`.
- **D3.** Mô hình miền là dataclass bất biến (`frozen=True`). Thực thể lưu xuống kho là bản sao dạng dict, không lộ đối tượng của thư viện ngoài.
- **D4.** `core` không import gói nào khác. `context`, `llm` và `evaluation` không import `bot`. Chỉ `pipeline` và `cli` nối các gói.
- **D5.** Quy tắc D4 được kiểm tra bằng một test dùng `ast` đọc các import, chạy trong `make test`. Chưa dùng import-linter.

## Phương án khác

- **Không dùng cổng, gọi thẳng công cụ:** nhanh hơn lúc đầu nhưng mỗi thay đổi ở Z đụng vào pipeline.
- **Dùng thư viện ABC hoặc injector:** nặng hơn cần thiết cho quy mô này. `Protocol` đủ cho kiểm tra kiểu bằng mypy.

## Hệ quả

- **Tốt hơn:** thay Jenkins, SCM, mô hình hay công cụ quét bằng cách viết một bộ chuyển đổi. Test pipeline bằng bộ giả.
- **Tệ hơn:** thêm một lớp gián tiếp, và phải giữ cổng ổn định sớm.
- **Từ nay phải đúng:** thay đổi một cổng là thay đổi cần được review vì nó ảnh hưởng mọi bộ chuyển đổi.
