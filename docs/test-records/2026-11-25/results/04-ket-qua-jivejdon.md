# Kết quả: A/B/C trên repo jivejdon

**Mô hình LLM: Claude Sonnet 5.5 (`claude-sonnet-5-5`), effort `medium`**, gọi qua `claude -p` (xem [kịch bản](../scenarios/04-kich-ban-jivejdon.md)). Ngày chạy 2026-11-25.

## Tóm tắt

- 18 commit, 30 cảnh báo mới của A. 28 cảnh báo nằm trong file Java mà commit sửa, khớp bảng đăng ký. 2 cảnh báo còn lại nằm ở file JavaScript lớn không thuộc diff (xem mục Bất thường) và bị loại khỏi số đo.
- 18/18 lượt chạy `status=ok`, 60/60 lời gọi LLM thành công, không lỗi, không hết trần token.
- Trên 28 cảnh báo: **B giữ 9, loại 11, `unknown` 8; C giữ 6, loại 13, `unknown` 9.** B và C cùng nhãn ở 21/28 cảnh báo.
- **Chưa có nhãn người**, nên chưa tính được tỉ lệ loại đúng cảnh báo sai (FP-removal) hay tỉ lệ loại nhầm lỗi thật (TP-loss). Bảng dưới chỉ cho biết bot giữ hay loại.

## Theo luật Semgrep (28 cảnh báo trong file đổi)

| Luật | n | B giữ/loại/unknown | C giữ/loại/unknown |
|---|---|---|---|
| `crlf-injection-logs` | 12 | 4/8/0 | 2/8/2 |
| `no-direct-response-writer` | 4 | 0/2/2 | 0/4/0 |
| `unsafe-reflection` | 3 | 0/0/3 | 1/0/2 |
| `insecure-trust-manager` | 3 | 3/0/0 | 1/0/2 |
| `unvalidated-redirect` | 3 | 0/0/3 | 0/0/3 |
| `weak-ssl-context` | 1 | 1/0/0 | 1/0/0 |
| `disallow-old-tls-versions1` | 1 | 1/0/0 | 1/0/0 |
| `use-of-md5` | 1 | 0/1/0 | 0/1/0 |

Nhận xét:

- `crlf-injection-logs` (CWE-93, 12 cảnh báo) chiếm nhiều nhất. B và C loại 8/12, thường với lý do tham số đã qua `StringUtils.isNumeric` hoặc `new Long(...)` trước khi vào log.
- `unvalidated-redirect` và `unsafe-reflection`: gần như toàn `unknown`. Lý do LLM nêu: không thấy thân hàm kiểm tra `isSameOriginReferer`, hoặc không thấy mảng tên lớp lấy từ đâu.
- `insecure-trust-manager`: B giữ cả 3. C giữ 1, trả `unknown` 2 vì đoạn mã chỉ cho thấy một phương thức của TrustManager.
- C loại nhiều hơn B ở `no-direct-response-writer` (4/4 so với 2/4), nhờ thấy `escapeHtml` trong ngữ cảnh.

## Theo commit

| PR | Commit | Ngày | A | B giữ/loại/unknown | C giữ/loại/unknown | Thời gian (s) | Token |
|---|---|---|---|---|---|---|---|
| 1 | `b039487b` | 2018-12-19 | 1 | 0/1/0 | 0/1/0 | 178 | 13.750 |
| 2 | `aec8145c` | 2018-12-21 | 2 | 0/1/1 | 0/2/0 | 176 | 19.097 |
| 3 | `b69377d8` | 2018-12-21 | 1 | 0/1/0 | 0/1/0 | 178 | 13.564 |
| 4 | `dcbc6f69` | 2018-12-22 | 2 | 0/2/0 | 0/2/0 | 178 | 22.797 |
| 5 | `c75d54b2` | 2019-01-31 | 3 | 0/0/3 | 1/0/2 | 178 | 25.641 |
| 6 | `a57f341f` | 2019-05-21 | 1 | 1/0/0 | 1/0/0 | 179 | 11.243 |
| 7 | `2aba86e4` | 2023-08-03 | 5 | 5/0/0 | 3/0/2 | 188 | 27.347 |
| 8 | `a0d85591` | 2023-12-07 | 1 | 0/1/0 | 0/1/0 | 172 | 12.730 |
| 9 | `0ee1030f` | 2023-12-07 | 3 | 1/2/0 | 1/2/0 | 192 | 33.873 |
| 10 | `547d112c` | 2024-01-30 | 1 | 1/0/0 | 0/0/1 | 179 | 14.573 |
| 11 | `6f6e8981` | 2024-01-31 | 1 | 1/0/0 | 0/0/1 | 181 | 14.611 |
| 12 | `7aa40908` | 2024-07-27 | 1 | 0/1/0 | 0/1/0 | 167 | 5.035 |
| 13 | `78b05e41` | 2025-07-23 | 1 | 0/1/0 | 0/1/0 | 172 | 11.379 |
| 14 | `1d7ce642` | 2025-10-06 | 1 | 0/1/0 | 0/1/0 | 171 | 11.868 |
| 15 | `96591992` | 2026-09-30 | 2 | 0/0/2 | 0/1/1 | 172 | 12.828 |
| 16 | `8a6a084d` | 2026-10-16 | 1 | 0/0/1 | 0/0/1 | 170 | 7.675 |
| 17 | `0546bf48` | 2026-10-16 | 2 | 0/1/1 | 0/1/1 | 177 | 103.364 |
| 18 | `d4dbd949` | 2026-10-18 | 1 | 0/0/1 | 0/0/1 | 169 | 7.541 |

A, giữ, loại, `unknown` tính trên mọi cảnh báo của lượt chạy, gồm cả 2 cảnh báo ngoài diff ở PR 2 và PR 17.

## Chi phí và thời gian

| Mục | Giá trị |
|---|---|
| Thời gian một lượt chạy (trung vị, min–max) | 177 s (167–192 s). Phần lớn là Semgrep quét toàn repo ở base và head |
| Thời gian một lời gọi LLM (trung vị, max) | 8,6 s (16,2 s) |
| Token (vào/ra, cả 60 lời gọi) | 324.057 / 44.859. Token vào gồm phần nền của Claude Code, khoảng 900 token mỗi lời gọi |
| Chi phí | Tính vào gói Claude Code. Giá API tương đương theo Claude Code: khoảng 1,63 USD cho 60 lời gọi |

## Ca điển hình

Nhãn người để trống, chỉ điền sau khi gán mù.

1. **PR 9, `SmsQQAction.java:48` (CRLF trong log): B và C cùng giữ.** Điều kiện `!StringUtils.isNumeric(phoneNumber)` dẫn chính giá trị không phải số (có thể chứa `\r\n`) vào nhánh ghi log. Phép kiểm tra không chặn mà còn mở đường.
2. **PR 9, `MessageListNav2Action.java:41`: B và C cùng loại.** Tham số đã qua `isNumeric` trước khi vào log nên chỉ có chữ số. C ghi rõ giả định `StringUtils` là của commons-lang.
3. **PR 10, `AccountProfileAction.java:68`: B giữ, C `unknown`.** Ngữ cảnh luồng dữ liệu cho C thấy regex `illEscape` ở `AccountFactoryDao` (hàm khác) có thể chặn chuỗi xấu. Đây là loại ca mà ngữ cảnh của C đổi kết luận.
4. **PR 16, `RefererCaptchaAction.java:102` (chuyển hướng không kiểm tra): cả hai `unknown`.** Kết luận phụ thuộc hàm `isSameOriginReferer` mà LLM không thấy thân hàm.
5. **PR 5, `FiltersAction.java:237` (`Class.forName` từ request): B `unknown`, C giữ.** C thấy tham số `classname` lấy thẳng từ request và không có whitelist.

## Bất thường

- **Semgrep không ổn định trên file JavaScript lớn.** Cùng một cặp base/head, cảnh báo `detect-non-literal-regexp` ở `prototype.js` (92 KB) và `jquery-2.1.1.js` lúc có lúc không giữa các lần chạy. Hai cảnh báo JS lúc lọc (PR 5, PR 12) không xuất hiện lần này, còn hai cảnh báo JS khác (PR 2, PR 17) xuất hiện ở file không thuộc diff. Giả thuyết: Semgrep hết thời gian khi quét file lớn ở một phía, nên cảnh báo cũ bị tính là "mới". Chưa chứng minh.
- **`pr-triage replay` đếm sai cảnh báo mới** ở roller và jspwiki (lần lọc trước khi đổi sang jivejdon): 10/10 PR được chọn có cảnh báo nằm ngoài file PR sửa, còn `pr-triage run` cho 0. Có thể cùng nguyên nhân với mục trên. Vì vậy jivejdon được lọc bằng `run`, không bằng `replay`.
- **OpenRouter không dùng được trong ngày:** khóa xác thực được nhưng mọi lời gọi mô hình, kể cả Playground trên web, trả HTTP 400 "Request path cannot be relayed". Đây là lý do dùng Claude qua `claude -p`.

## Giới hạn

- **Chưa có nhãn người:** mọi nhận xét "đúng/sai" ở trên là của LLM, chưa được kiểm chứng.
- **Kém tái lập hơn API:** `claude -p` không đặt được `temperature` và `seed`. Chưa đo độ ổn định giữa các lần chạy.
- **Nhãn bot nhiều `unknown`** (B 8/28, C 9/28). Chính sách hiển thị (mặc định theo B) chỉ thu gọn cảnh báo `likely_false`; cảnh báo `unknown` vẫn hiện đầy đủ, nên tỉ lệ cảnh báo được ẩn thấp hơn tỉ lệ "loại".
- **Một repo, một tác giả chính,** thông điệp commit thường chỉ là "fixed". Cảnh báo lệch về CWE-93.
- **Repo công khai từ 2018,** có thể đã nằm trong dữ liệu huấn luyện của mô hình.

## Tái lập

Dữ liệu thô (kết quả từng lượt, store SQLite, nhật ký từng lời gọi LLM, bảng từng cảnh báo) nằm ngoài Git, ở `data/raw/jivejdon-*` và `data/team/store-claude.sqlite` trên máy người chạy. Script lọc và chạy: `data/raw/prefilter_changed.py`, `confirm_run.py`, `run_bc_jivejdon_claude.py`, cầu nối `claude_bridge.py`.
