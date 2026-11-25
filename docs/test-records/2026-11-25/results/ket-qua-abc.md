# Kết quả chạy A, B, C — logicaldoc và mesh, 2026-11-25

Kịch bản: [02](../scenarios/02-chay-a-b-c.md). Bảng đăng ký: [dang-ky-pr.md](dang-ky-pr.md). Số liệu dưới đây tính
từ `triage-result.json` của 13 lượt `pr-triage run`. File thô, bảng theo PR, comment và ảnh nằm trong gói nộp riêng,
không commit.

**Giữ mù cho bước gán nhãn:** hồ sơ này chỉ có số tổng của cả hai repo. Không ghi nhãn B, C theo PR hay theo cảnh
báo, và không tách `likely_true` với `likely_false`, để người gán nhãn (mục 6 của hướng dẫn) không bị ảnh hưởng.

## Cấu hình

| Mục | Giá trị |
|---|---|
| Lệnh | `pr-triage run --base <merge-base> --head <head> --pr=<số> --variants B,C --no-secrets --snippet-radius 40 --display C --budget-pr-tokens 3000000 --db data/team/store.sqlite` |
| Mã | `main` @ `81929df`, prompt `v1`, Semgrep CE 1.185.0 với `p/default` (1074 luật, khớp `rulesets.lock`) |
| Mô hình | DeepSeek có chế độ suy luận, qua một cổng tương thích OpenAI khác cổng của nhóm. `temperature=0`, `seed=0`, `max_tokens=1500` (mặc định của client). Tên mô hình chỉ ghi trong nhật ký nộp riêng |
| Trần thời gian quét | 1.200 giây mỗi lượt quét (mặc định 300), giống phần lọc A. Trần 30 giây mỗi file giữ nguyên |
| Máy | Máy chủ Linux dùng chung, 16 lõi, có job khác. Hai luồng chạy song song, mọi tiến trình chạy với `nice` |

## Số liệu tổng

| | Giá trị |
|---|---|
| Lượt `run` | 13 (10 PR logicaldoc, 3 PR mesh), không lượt nào `failed` |
| Trạng thái | 6 `ok`, 7 `degraded` |
| Cảnh báo của A | 56. Mỗi cảnh báo có đúng một nhãn B và một nhãn C |
| Thời gian một lượt | trung vị 501 giây, lớn nhất 695 giây, tổng 6.048 giây. Phần lớn là hai lượt quét Semgrep trên máy bận |
| Độ trễ một lần gọi LLM | trung vị 8,2 giây, lớn nhất 21,2 giây (108 lần gọi có ghi độ trễ, gồm cả lần gọi sửa) |
| Token B và C | 239.761 vào, 188.508 ra |

| Nhãn | B | C |
|---|---|---|
| Có kết luận (`likely_true` hoặc `likely_false`) | 32 | 28 |
| `unknown` do mô hình trả | 12 | 13 |
| `invalid`: đầu ra bị cắt cụt (`finish_reason=length`) cả ở lần gọi sửa | 12 | 11 |
| `unknown` do lỗi đường truyền (HTTP 403), mô hình chưa nhận request | 0 | 4 |
| **Tổng** | **56** | **56** |

## Sự cố khi chạy và cách xử lý

| Sự cố | Ảnh hưởng | Xử lý |
|---|---|---|
| Hai tiến trình cùng khởi tạo file SQLite mới: `database is locked` | 1 lượt hỏng sau 2 giây | Chạy lại sau khi luồng chính xong, `ok` |
| Quét Semgrep quá trần 300 giây | 2 lượt `failed` | Nâng trần lên 1.200 giây như phần lọc A, chạy lại, cả hai xong |
| Lớp chống bot trước cổng LLM trả trang HTTP 403 | 4 nhãn C, đều thuộc luật `unsafe-reflection`, ở 3 PR | Thêm thử lại 3 lần (chờ 20, 40, 60 giây) và chạy lại 2 PR bị trước khi có thử lại. Cả 4 nhãn vẫn bị 403 sau mỗi lần thử, còn nhãn B của cùng cảnh báo thì qua. Nghi là bị chặn theo nội dung ngữ cảnh của C, chưa xác định chuỗi nào |
| Đầu ra bị cắt cụt | 23 nhãn (12 B, 11 C) ở 4 PR | Không xử lý, giữ làm kết quả đo. Xem giới hạn 2 |

## Giới hạn và điều chưa kiểm chứng

1. **Mô hình khác mô hình đã khóa** ở `eval-freeze-1`, nên `manifest_hash` khác và số liệu này không gộp thẳng được
   với đợt đánh giá chính. Phần A (lọc, bảng đăng ký) không phụ thuộc mô hình. Muốn so được thì chạy lại B, C trên
   cùng bảng đăng ký bằng mô hình đã khóa.
2. **Tỉ lệ cắt cụt cao: 23/112 nhãn (21%).** Mô hình suy luận trước khi trả lời và token suy luận bị tính vào
   `max_tokens=1500`. 22/23 nhãn bị cắt thuộc luật `no-direct-response-writer` ở các servlet dữ liệu, 1 thuộc
   `formatted-sql-string`. Đợt đánh giá OSS ngày 2026-11-18 có 15/242. Lượt này không tăng `max_tokens` và không tắt chế độ suy luận, vì đổi tham số sau khi
   thấy đầu ra là tinh chỉnh trên dữ liệu đánh giá. Nhóm nên chốt `max_tokens` (hoặc mô hình) trước đợt chạy sau.
3. **4 nhãn C bị 403 nên loại khỏi mẫu số của C** khi tính chỉ số (lọc theo trường `error` bắt đầu bằng
   `llm_error: HTTP 403`). Đây là lỗi hạ tầng, không phải phán đoán của mô hình.
4. **Chưa có nhãn đáp án.** Nhãn B và C là đầu ra đang được đánh giá. Nhãn đáp án do người trong nhóm gán chéo và mù.
   Chưa tính độ chính xác, độ phủ hay tỉ lệ giảm cảnh báo.
5. **Mẫu nhỏ và lệch luật:** 13 PR, 56 cảnh báo, trong đó 34 cảnh báo `no-direct-response-writer` của logicaldoc đến
   từ 3 commit đổi cách ghi chuỗi (xem [loc-a.md](loc-a.md)). Mô hình có thể đã thấy mã của hai repo này khi huấn luyện.
6. **Dữ liệu chứa giá trị công khai nhạy cảm:** một PR của mesh có cảnh báo trên `js/.npmrc`; `mask()` không che mẫu
   `_auth=` nên giá trị nằm nguyên trong kết quả thô (nợ TD-9). Không chép giá trị này vào báo cáo hay slide.
