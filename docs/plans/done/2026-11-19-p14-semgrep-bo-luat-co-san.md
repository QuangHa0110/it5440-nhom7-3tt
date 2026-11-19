# P14. Thay luật Semgrep tự viết bằng bộ luật có sẵn `p/default`, chạy từ bản tải về được khóa bằng mã băm

- **Status:** done
- **Người làm:** hadvq (với Claude Code)
- **Đóng:** một nửa TD-2 (chốt công cụ quét; ngôn ngữ chính vẫn mở)
- **Quyết định cho phép:** hadvq chọn `p/default` ngày 2026-11-19, sau khi so 5 bộ luật trên repo demo; ghi thành ADR 0015 ở T1
- **Nhánh:** `hadvq/scan/semgrep-p-default`, tách từ nhánh P13 (`hadvq/deploy/jenkins-central-job`) vì PR #7 chưa merge; rebase lên `dev` khi PR #7 merge
- **Bắt đầu / Kết thúc:** 2026-11-19 / 2026-11-19

---

## Bối cảnh

Bot đang quét bằng 3 luật nhóm tự viết, chỉ phủ SQL injection (`configs/semgrep/java-injection.yml`). Có hai lý do phải đổi ngay, trước khi chạy ở công ty Z:

1. **Z chưa có công cụ phân tích tĩnh nào trong CI** (người dùng xác nhận 2026-11-18). Cấu hình A giờ có nghĩa là "Z chỉ cài Semgrep", nên bộ luật phải là bộ một công ty thật sẽ cài. Nếu vẫn dùng luật tự viết thì RQ1 và RQ2 không đại diện cho thực tế.
2. **Không được thiên vị cho LLM.** Bộ nhiều tiếng ồn (`p/security-audit`, `p/findsecbugs`) sẽ làm tỉ lệ báo sai nền cao giả tạo, khiến bộ lọc trông tốt hơn thật. Ngược lại, bộ quá sạch (`p/java`) để bộ lọc gần như không có việc.

`p/default` là bộ Semgrep khuyến nghị mặc định cho CI. Nó chứa trọn `p/java` và thêm các luật độ tin cậy thấp, phủ mọi ngôn ngữ.

**Ràng buộc giấy phép.** Bộ luật dùng Semgrep Rules License v1.0: được dùng nội bộ, **không được phân phối lại**. Repo này là public, nên file luật **không bao giờ được commit**. Luật được tải về trong hạ tầng nơi chạy bot (máy dev, image Jenkins của Z), lưu dưới `data/` (đã có trong `.gitignore`). Repo chỉ giữ tên bộ luật, ngày tải và mã băm.

## Ngoài phạm vi

- **FindSecBugs/SpotBugs** (ADR 0005 D1): hoãn. ADR 0015 ghi lý do. Có thể làm sau, như công cụ quét thứ hai.
- **Chạy lại BenchmarkJava** với bộ luật mới: thuộc phần đánh giá (P07), sẽ làm trong kế hoạch riêng sau khi có cổng LLM và người chạy.
- **Lọc luật theo ngôn ngữ của Z:** chưa biết Z viết bằng ngôn ngữ gì. Script T2 có sẵn tùy chọn lọc, nhưng mặc định giữ đủ bộ.
- **Không xóa** `java-injection.yml`. Các test dùng nó vì cần chạy không có mạng và có kết quả cố định.
- **Không đổi** prompt, LLM, dấu vân tay hay cách hiển thị comment.

## Hiện trạng đã kiểm chứng

Kiểm tra ngày 2026-11-18 và 2026-11-19, Semgrep 1.186.0, bộ luật tải về scratchpad bằng `curl https://semgrep.dev/c/p/<tên>`, không đưa vào repo.

- Số luật: `p/default` có 1074 luật, trong đó 118 luật Java, 21 luật taint; độ tin cậy Java: cao 32, trung bình 41, thấp 45. `p/java` có 60 luật và là tập con của `p/default`. Phần Java của `p/owasp-top-ten` trùng hệt `p/java`.
- Trên 7 nhánh của repo demo:
  - PR #1 và #3 (SQLi thật): bắt được bằng hai luật `formatted-sql-string` và `jdbc-sqli` trên cùng một dòng.
  - PR #6 (nối chuỗi số nguyên): `jdbc-sqli` (độ tin cậy thấp) báo; `p/java` không báo.
  - Mọi nhánh: thêm cảnh báo XSS `no-direct-response-writer` ở `UserController.java:20` (có sẵn ở `main`). PR #1 đến #3 có thêm một cảnh báo này ở dòng 30.
- Thời gian quét một nhánh demo: `p/java` khoảng 7 giây, `p/default` khoảng 23 giây (phần lớn là nạp luật).
- **Gộp cảnh báo trùng đã có:** `normalize/ops.py:70` `deduplicate` gộp theo CWE, file, hàm và vùng chồng nhau, và được gọi ở `pipeline/runner.py:150`. Hai luật SQLi trên cùng dòng *nên* được gộp. Chưa kiểm tra với CWE thật của `p/default`.
- **Manifest băm nội dung file luật:** `pipeline/build.py:43-46`. Nếu truyền tên registry (`p/default`) thì chỉ băm chuỗi tên, nên không khóa được nội dung. Vì vậy phải chạy từ file đã tải về.
- **Mã luật có tiền tố đường dẫn:** khi chạy file luật cục bộ, Semgrep ghép đường dẫn thư mục vào `check_id`. `scan/semgrep.py` đọc lại `id:` trong file (`_local_rule_ids`) để bỏ tiền tố. Cần test để chắc dấu vân tay không đổi khi chuyển file luật sang thư mục khác.
- **Danh mục sink của cách C** (`configs/context/java.yml`) chỉ có CWE-89, 78, 79, 22, 90 và 643. Trong khi đó, các CWE Java nhiều nhất của `p/default` là 319, 89, 327, 611, 326, 502 và 94.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | ADR 0015 "Bộ luật Semgrep `p/default`, tải về và khóa bằng mã băm": bối cảnh, quyết định, phương án khác (5 bộ đã so, FindSecBugs, Opengrep), hệ quả giấy phép. Thêm ghi chú có ngày trong ADR 0005 trỏ sang 0015. Cập nhật TD-2 | `docs/adr/0015-*.md` tồn tại; ADR 0005 có dòng trỏ sang 0015; TD-2 ghi rõ phần đã đóng | — |
| T2 | `scripts/fetch_semgrep_rules.py`: tải `https://semgrep.dev/c/p/<tên>` vào `data/rules/semgrep-<tên>.yml`. Tùy chọn `--languages` để lọc. Kiểm tra YAML hợp lệ. Ghi `configs/semgrep/rulesets.lock` gồm tên, URL, ngày tải, sha256, số luật, phiên bản Semgrep (không chứa nội dung luật). Có `--verify` để so file hiện có với lock | Test với HTTP giả: tải → lock đúng sha256; sửa 1 byte → `--verify` thoát mã khác 0. Sau khi chạy thật, `git status` không hiện file nào dưới `data/` | T1 |
| T3 | Pipeline dùng bản đã khóa: `build.py`, `app/settings.py`, `Dockerfile`, `deploy/jenkins/triage.Jenkinsfile` mặc định trỏ tới `data/rules/semgrep-default.yml`. Khi khởi động, kiểm tra sha256 với `rulesets.lock`; lệch thì dừng với thông báo rõ. Image Jenkins tải luật lúc build rồi `--verify`. Test vẫn truyền `java-injection.yml` rõ ràng | Test: file luật lệch lock → `ScanError` có thông điệp nhắc chạy lại script. `make test` qua. Build image Jenkins có file luật và qua `--verify` | T2 |
| T4 | Test chống trôi dấu vân tay: cùng một luật, đặt ở hai thư mục khác nhau → cùng `rule_id` và cùng dấu vân tay. Test gộp: hai luật CWE-89 trên cùng dòng → một cảnh báo với `rule_ids` có cả hai | Hai test mới qua (dùng luật nhỏ trong `tests/fixtures/`, không dùng file của registry) | T3 |
| T5 | Cách C với CWE ngoài danh mục: kiểm tra một cảnh báo CWE-327 (mật mã yếu) đi qua `DataflowProvider` mà không lỗi, bundle ghi rõ "không áp dụng luồng dữ liệu". Thêm sink cho CWE-611 (XXE), 502 (deserialization), 94 (code injection), 918 (SSRF) vào `configs/context/java.yml` | Test: finding CWE-327 → bundle có ghi chú, không ngoại lệ; finding CWE-502 có sink `readObject` → C tìm được nguồn trên fixture | T3 |
| T6 | Chạy lại 6 PR demo bằng `p/default` (cổng LLM thật nếu có). Cập nhật bảng kịch bản trong `docs/demo.md`, chú ý cảnh báo XSS mới ở PR #1 đến #3 | `docs/demo.md` khớp kết quả chạy; ghi số cảnh báo, token và thời gian mỗi PR vào devlog | T3–T5 |
| T7 | Đo thời gian quét `p/default` trên một repo Java công khai cỡ vừa (vd. BenchmarkJava, khoảng 2.700 file), cả quét toàn repo và chỉ file thay đổi | Devlog ghi thời gian hai trường hợp; nếu toàn repo quá 10 phút thì ghi đề xuất lọc theo ngôn ngữ hoặc chỉ quét file thay đổi | T2 |

T7 độc lập với T3–T6, làm song song được.

## Cổng

```bash
make check
uv run python scripts/fetch_semgrep_rules.py --verify
```

Chạy thêm một PR demo đầu cuối bằng `p/default`; comment phải có cảnh báo SQLi ở PR #1. `git status` không có file nào dưới `data/`.

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì khi xảy ra |
|---|---|---|
| Hiểu sai giấy phép: dùng luật trong việc nhóm làm cho Z bị coi là "tư vấn" cần mua giấy phép | Điều khoản hoặc Semgrep nói vậy | Để Z tự tải và chạy luật trong hạ tầng của Z, nhóm chỉ cung cấp script. Nếu vẫn vướng thì cân nhắc Opengrep và bộ luật của Opengrep (cần kiểm tra giấy phép) |
| Máy Jenkins của Z không ra được internet | Script T2 lỗi kết nối khi build image | Tải trên máy khác trong Z, chép vào, chạy `--verify` với lock |
| URL `semgrep.dev/c/p/...` đổi hoặc cần đăng nhập | HTTP 401/404 hoặc nội dung không phải YAML | Script báo lỗi rõ; thử `semgrep scan --config p/default --dump-config` hoặc tải từ trang registry |
| Bộ luật trên registry đổi giữa hai lần tải | `--verify` báo lệch sha256 | Đúng ý đồ: không tự cập nhật. Muốn đổi thì chạy lại script, commit lock mới, và phải trước khi gắn tag khóa eval |
| `p/default` báo quá nhiều trên mã của Z, comment dài | Hơn `max_findings` (40) cảnh báo mỗi PR | Giữ nguyên bộ luật cho số liệu; chỉ cắt khi hiển thị bằng `limits.max_findings` và `severity.min_comment`, ghi vào devlog |
| Cảnh báo trùng không được gộp vì hai luật ghi CWE khác nhau cho cùng một lỗi | Một dòng hiện hai cảnh báo trong comment | Ghi devlog; cân nhắc gộp theo nhóm CWE (89 với 564), không gộp theo dòng không điều kiện |
| Quét chậm trên repo lớn | T7 đo quá 10 phút | Lọc luật theo ngôn ngữ của Z bằng `--languages`, hoặc chỉ quét file thay đổi ở nhánh đích |

---

## Kết quả

*Điền khi đóng kế hoạch. Không sửa phần thân phía trên.*

*Ghi chú 2026-11-19, khi đóng.*

- **Kết quả:** Bot chạy bằng `p/default` tải về `data/rules/`, khóa bằng `configs/semgrep/rulesets.lock`; thiếu hoặc lệch mã băm thì dừng (CLI thoát mã 2, máy chủ App không khởi động). Hai luật SQLi cùng dòng gộp thành một cảnh báo. Cách C có thêm sink cho CWE-611, 502, 94, 918, 601, 23 và ghi "không áp dụng luồng dữ liệu" cho các CWE cấu hình hoặc thuật toán. Sáu PR demo chạy lại, `docs/demo.md` cập nhật. BenchmarkJava toàn repo quét trong 130 giây.
- **Khác kế hoạch ở đâu:**
  - T3: luật được **gắn vào container bằng volume chỉ đọc** từ `data/rules` của máy chủ, không tải lúc build image. Lý do: image không chứa bản sao luật (giấy phép), và Jenkins của Z có thể không ra được internet lúc build. Chưa build image Jenkins để kiểm tra.
  - T4 lộ ra lỗi thật: id luật từ file JSON của registry mang đường dẫn tuyệt đối, làm dấu vân tay phụ thuộc máy. Đã sửa (`fix(scan)`). Fixture luật viết ngay trong test, không thêm file vào `tests/fixtures/`.
  - T5: thêm CWE-601 và CWE-23 ngoài bốn CWE dự kiến, và danh sách `no_dataflow_cwes`, dựa trên đếm CWE thật của luật Java.
  - T6: máy không có khóa LLM nên chỉ đo phía công cụ quét, chưa có số token. PR 02 không còn im lặng (XSS có cơ sở ở `doPost`); chưa sửa mã demo.
  - Cổng: ruff, mypy, `--verify` qua; `git status` không có file dưới `data/`. `make check` trên Windows còn 4 test hỏng có từ trước (đường dẫn `\`, TD-3), CI Linux không bị. Chưa chạy demo đầu cuối với LLM thật.
- **Ghi ở:** devlog `2026-11-19-p14-bo-luat-p-default.md`, nợ TD-3, ADR 0015.
