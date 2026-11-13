# `docs/plans/` — vòng đời kế hoạch

Kế hoạch là một đơn vị công việc có thể commit, với điều kiện hoàn thành quan sát được. Thư mục cho biết trạng thái, nên trả lời "đang làm gì" bằng `ls`.

| Bucket | Ý nghĩa | Ai chuyển, khi nào |
|---|---|---|
| `queued/` | Sẵn sàng chạy, có thứ tự. Chưa ai làm | Tác giả, khi viết xong |
| `active/` | Đang có người làm. Mỗi kế hoạch một người nhận | Người làm, khi bắt đầu |
| `done/` | Xong, điều kiện hoàn thành đã được kiểm chứng | Người làm, ở commit đóng |
| `failed/` | Bỏ dở hoặc bị thay thế, giữ lại kèm lý do | Người làm, khi dừng |

- Tên: `YYYY-MM-DD-<slug>.md` (hoặc thư mục cùng tên nếu có tài liệu kèm). Bắt đầu từ [_template.md](_template.md).
- Chuyển bucket bằng `git mv`, không sao chép.
- `done/` và `failed/` là hồ sơ lịch sử: chú thích bằng ghi chú có ngày, không viết lại phần thân.
- Công cụ Claude Code ghi kế hoạch mới vào `queued/` (xem `.claude/settings.json`), người làm chuyển tay sang `active/`.
- Cần kế hoạch khi việc có từ 3 task trở lên.

## Thứ tự trong `queued/`

Mục tiêu: **hệ thống chạy được đầu cuối** (`make e2e`) trên một repo Java thử, với cổng LLM thật.

| # | Kế hoạch | Phụ thuộc | Mốc kiểm chứng |
|---|---|---|---|
| P01 | [Mô hình miền, cổng và kho](queued/2026-11-13-p01-core-va-store.md) | — | `make check` |
| P02 | [Quét và chuẩn hóa](queued/2026-11-13-p02-scan-va-normalize.md) | P01 | Cách A chạy được |
| P03 | [LLM và cách B](queued/2026-11-13-p03-llm-va-cach-b.md) | P01, P02 T4 | Cách B trên cổng thật |
| P04 | [Ngữ cảnh luồng dữ liệu](queued/2026-11-13-p04-ngu-canh-luong-du-lieu.md) | P02 | Cách C và số đo `missing` |
| P05 | [Pipeline và CLI](queued/2026-11-13-p05-pipeline-va-cli-chay-duoc.md) | P01 đến P04 | `make e2e` **(hệ thống chạy được)** |
| P06 | [Bot và phản hồi](queued/2026-11-13-p06-bot-va-phan-hoi.md) | P05 | Comment một lần, phản hồi theo cảnh báo |
| P07 | [Đánh giá ngoại tuyến](queued/2026-11-13-p07-evaluation.md) | P05 | Số đo trên BenchmarkJava |

P02 và P03 có thể làm song song sau P01. P04 và P03 độc lập nhau.

## Quy tắc chạy xuyên đêm

Áp dụng khi người dùng giao cho Claude Code chạy các kế hoạch trên mà không có mặt.

1. Mỗi kế hoạch một nhánh cá nhân tách từ `dev` cục bộ, mỗi task một commit. **Không push, không mở PR.**
2. Cổng của kế hoạch qua thì `git mv` sang `done/` và ghi mục Kết quả. Chưa qua thì để ở `active/`.
3. Gặp điều bất ngờ hoặc kết quả đo làm lung lay một ADR thì ghi vào `docs/devlog/` rồi đi tiếp bằng phương án an toàn. Không tự sửa ADR đã `accepted`.
4. **Dừng và để lại ghi chú** khi: cần quyết định không có trong ADR, cổng LLM không dùng được sau 3 lần thử cách nhau, một task lỗi sau 3 lần sửa, hoặc phải chạm vào thứ nằm ngoài repo.
5. Khóa API chỉ lấy từ biến môi trường. Không ghi vào file, log, commit hay devlog.
6. Không gửi mã của công ty Z tới cổng LLM ngoài. Dữ liệu thử là mã nguồn mở công khai.
7. Cuối phiên viết bản tóm tắt vào `docs/devlog/` gồm: đã xong, đang dở, các quyết định tự đưa ra, lệnh để tái chạy.
