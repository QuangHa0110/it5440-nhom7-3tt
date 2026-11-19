# P14: chuyển sang bộ luật `p/default`, những điều bất ngờ

- **Ngày:** 2026-11-19. Kế hoạch P14, ADR 0015.

## Id luật mang theo đường dẫn tuyệt đối của máy

Bộ `p/default` tải từ registry là **JSON một dòng**, không phải YAML nhiều dòng như file luật tự viết. Hàm `_local_rule_ids` đọc id bằng regex `- id:` nên không bắt được id nào (0/1074). Hệ quả: Semgrep gắn đường dẫn thư mục chứa file luật vào trước id, ví dụ `D.<thư mục repo>.data.rules.java.lang.security.audit.sqli.jdbc-sqli.jdbc-sqli`, và bot không bỏ được tiền tố này.

Tác hại nếu không bắt được:

- **Dấu vân tay đổi theo máy.** Máy dev, container Docker (`/app/data/rules`) và Jenkins (`/opt/pr-triage/data/rules`) cho id khác nhau. Mọi cảnh báo cũ sẽ bị coi là "mới" khi đổi nơi chạy, và số liệu đánh giá giữa các máy không so được.
- **Đường dẫn nội bộ lọt vào comment và cơ sở dữ liệu.** Trái quy tắc không lộ đường dẫn nội bộ.

Đã sửa ở commit `fix(scan)`: đọc id bằng trình parse YAML (đọc được cả JSON), giữ regex làm dự phòng. Parse 1074 luật mất dưới 1 giây. Test `tests/scan/test_registry_rule_ids.py` đặt cùng một file luật ở hai thư mục khác nhau và kiểm tra id cùng dấu vân tay giống hệt nhau.

## Phân bố CWE của luật Java trong `p/default`

Đếm từ file đã tải (118 luật Java, có luật mang nhiều CWE): nhiều nhất là CWE-319 (truyền dữ liệu không mã hóa, 17 luật), CWE-89 (14), CWE-327 (12), CWE-611 (9), CWE-326 (7), CWE-502 (6), CWE-94 (6). Chỉ 21 luật chạy ở chế độ taint.

Hệ quả cho cách C: gần một nửa số luật thuộc nhóm lỗi cấu hình hoặc chọn thuật toán (319, 327, 326, 328, 295, 352, 798...), nơi luồng dữ liệu không có ý nghĩa. Danh mục `configs/context/java.yml` nay có `no_dataflow_cwes` cho nhóm này; C gửi hàm chứa dòng bị báo và ghi "không áp dụng luồng dữ liệu" thay vì đoán sink. Danh mục cũng có thêm sink cho CWE-611, 502, 94, 918 như kế hoạch, cộng CWE-601 và CWE-23 vì chúng cũng xuất hiện trong luật Java.

## Sáu PR demo với `p/default`

Chạy bằng pipeline thật, LLM giả (máy không có khóa LLM), nên chỉ đo phía công cụ quét:

| PR | Cảnh báo mới sau gộp | Lượt luật trước gộp | Thời gian |
|---|---|---|---|
| 01 | 2 (CWE-89, CWE-79) | 3 | 18,8 s |
| 02 | 1 (CWE-79) | 1 | 19,5 s |
| 03 | 2 (CWE-89, CWE-79) | 3 | 19,2 s |
| 04 | 2 (CWE-798, bộ quét secret) | 2 | 21,1 s |
| 05 | 0 | 0 | 19,3 s |
| 06 | 1 (CWE-89, `jdbc-sqli` LOW) | 1 | 19,4 s |

- Hai luật SQL injection cùng dòng (`formatted-sql-string`, `jdbc-sqli`) được gộp thành một cảnh báo như thiết kế ADR 0011.
- **Bất ngờ:** PR 02 (truy vấn có tham số) không còn "im lặng". `p/default` báo XSS ở hàm `doPost` vì kết quả truy vấn được in thẳng ra response. Đây là cảnh báo có cơ sở, không phải lỗi gộp. `docs/demo.md` đã ghi lại; chưa sửa mã demo.
- Thời gian khoảng 19 giây mỗi PR, gấp khoảng 3 lần bộ luật tự viết (quét hai lần: nhánh đích và nhánh PR).
- Chưa có số token và nhận định LLM: cần chạy lại với khóa LLM thật (`make e2e`).

## Thời gian quét trên repo cỡ vừa (T7)

OWASP BenchmarkJava, bản clone nông commit `c6717ea` (2026-11-18), 2766 file Java, máy 8 nhân, Windows, Semgrep 1.185.0, bộ `p/default` đủ 1074 luật:

| Phạm vi | Thời gian | Cảnh báo |
|---|---|---|
| 10 file | 10,0 s | 2 |
| 50 file | 10,7 s | 33 |
| Toàn repo | 129,7 s | 3252 |

- Khoảng 10 giây là chi phí cố định để nạp luật, không phụ thuộc số file.
- Toàn repo dưới ngưỡng 10 phút của kế hoạch, nên chưa cần lọc luật theo ngôn ngữ.
- Pipeline hiện quét **toàn bộ** cả nhánh đích lẫn nhánh PR, nên một PR trên repo cỡ này mất khoảng 4 đến 5 phút chỉ cho bước quét. Nếu Z có repo lớn hơn nhiều, nên chỉ quét các file PR thay đổi ở cả hai nhánh (bộ chuyển đổi đã nhận tham số `paths`), khi đó còn khoảng 10 đến 20 giây.
- 3252 cảnh báo trên BenchmarkJava (nhiều nhất CWE-352, 89, 79, 326, 22, 78) chỉ cho thấy bộ luật ồn trên mã cố ý chứa lỗi. Không dùng làm số đánh giá: chạy BenchmarkJava đúng nghĩa thuộc kế hoạch đánh giá riêng.

## Test vốn đã hỏng trên Windows (không do P14)

Kiểm tra bằng `git stash` trước khi sửa: bốn test hỏng trên Windows từ trước, ghi ở TD-3.

- `tests/scan/test_semgrep_adapter.py::test_scan_sample_repo`, `tests/pipeline/test_semgrep_e2e.py::...contexts_differ`, hai test trong `tests/app/test_flow.py`: Semgrep trên Windows trả đường dẫn file dạng `src\app\X.java`.
- `tests/app/fakegithub.py` ghi file không chỉ định mã hóa, lỗi với tiếng Việt khi thiếu `PYTHONUTF8=1`.

CI chạy Linux nên không thấy. Trên Windows chạy test với `PYTHONUTF8=1`.
