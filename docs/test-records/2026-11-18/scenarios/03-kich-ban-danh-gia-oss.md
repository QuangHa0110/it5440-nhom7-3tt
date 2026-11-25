# Thiết kế kịch bản đánh giá PR Triage Bot (phương án mã nguồn mở)

> **Đợt 1** (cấu hình khóa bằng tag `eval-freeze-1`: 3 luật tự viết và 29 luật registry, trước ADR 0019). Quyết định ở ADR 0015–0017 (`docs/adr/`). Đợt 2 (luật `p/default`, dữ liệu mức PR, nhãn do người gán) theo `docs/huong-dan-chon-repo-va-pr.md`; số liệu hai đợt không gộp. Runbook từng lệnh nằm trong hồ sơ `.docs/` của nhóm, ngoài repo.


| | |
|---|---|
| Ngày | 2026-11-18 |
| Trạng thái | **Đã duyệt 2026-11-18** (gồm phần Jenkins tùy chọn, mục 5.8). **Sửa sau pilot:** nguồn dữ liệu và cách tách tập theo mục 6.3a. **Đã thực hiện 2026-11-18:** xem kết quả và báo cáo hoàn tất; còn D3, D4, J |
| Phạm vi dữ liệu | Tạm thời bỏ qua công ty Z. Đánh giá trên mã Java mã nguồn mở (hướng 3: kết hợp) |
| Gán nhãn | Claude gán nhãn toàn bộ, người kiểm tra mẫu (mục 6.5). **Lệch proposal mục 10**, cần ghi ADR và sửa proposal |
| Mô hình được đánh giá | Model cấu hình trong `.env` (`PR_TRIAGE_LLM_MODEL`, hiện là `deepseek/deepseek-v4.1-flash-1017`, cloud). Ghi model ID thực tế vào manifest |
| Căn cứ | proposal, test-plan, kế hoạch đánh giá, system-overview, ADR 0003/0009/0011, devlog 2026-11-13 về BenchmarkJava |

Ký hiệu: **[Quyết định của người dùng]** là điều anh/chị đã chốt trong hội thoại. **[Đề xuất]** là lựa chọn của người thiết kế, có thể sửa.

---

## 1. Mục đích

Cần một kịch bản đánh giá cụ thể, chạy được, trả lời hai câu hỏi tách biệt:

1. **Đánh giá mã (K):** mã nguồn của nhóm chạy đúng hay sai, sai ở đâu, sai nặng đến mức nào. Kết quả phải đủ chắc để tin rằng số liệu nghiên cứu không bị sai do lỗi phần mềm.
2. **Đánh giá kết quả (R):** so sánh A/B/C và đo giá trị thực của bộ lọc LLM theo RQ1–RQ4, với nhãn người làm đáp án.

Hai câu hỏi phải tách nhau. Mã có thể chạy đúng hoàn toàn mà LLM vẫn không đáng dùng, và đó vẫn là kết quả hợp lệ.

## 2. Mục tiêu, không mục tiêu, phản mục tiêu

**Mục tiêu**

- G1. Mọi ca P0/P1 trong test-plan có trạng thái rõ ràng (pass/fail/blocked/not run) và có bằng chứng.
- G2. Có cổng vào: điều kiện bắt buộc về chất lượng mã trước khi chạy tập `eval`.
- G3. Có pool tối thiểu **200 cảnh báo duy nhất** (60 `dev` / 140 `eval`) từ PR thật của repo Java mã nguồn mở, có nhãn tham chiếu do Claude gán mù, kiểm định bằng người trên mẫu.
- G4. Có bảng RQ1, RQ2 kèm mẫu số, khoảng tin cậy Wilson, McNemar B so với C, và giới hạn.
- G5. Có kết quả kiểm chéo với tập có sẵn đáp án (BenchmarkJava) và RQ4 trên Vul4J, ghi rõ đây là kiểm chéo.

**Không mục tiêu**

- Không tuyên bố kết quả "tại doanh nghiệp" hay "công ty Z".
- Không đo hành vi lập trình viên thật (RQ3 chỉ còn phần mô tả, xem mục 6.8).
- Không viết công cụ quét mới, không thêm cách D (agent), không tích hợp QLCoder.

**Phản mục tiêu** (nếu xảy ra thì coi là thất bại, kể cả khi số liệu đẹp)

- Chỉnh prompt hoặc tham số sau khi đã nhìn kết quả trên `eval`.
- Người gán nhãn (kể cả Claude) nhìn thấy nhận định của LLM. Vì vậy mỗi tập phải được gán nhãn **trước** khi chạy B/C trên tập đó.
- Trình bày nhãn do AI gán như nhãn của người.
- Gộp kết quả BenchmarkJava vào số liệu chính, hoặc dùng nó để kết luận C tốt hơn B.
- Bỏ `uncertain` khỏi mẫu số rồi gọi kết quả là "tỉ lệ cảnh báo sai toàn tập".
- Ghi số 0% khi mẫu số bằng 0.

## 3. Ràng buộc đã biết

| # | Ràng buộc | Hệ quả |
|---|---|---|
| C1 | Luật Semgrep tùy chỉnh chỉ có 3 luật SQL (`java-sqli-taint`, `java-sql-string-concat`, `java-sql-concat-flow`) | Muốn đủ cảnh báo phải thêm bộ luật registry, khóa phiên bản |
| C2 | Danh mục ngữ cảnh `configs/context/java.yml` có sink cho CWE-89, 78, 79, 22, 90, 643 | Phạm vi CWE của đánh giá là **nhóm injection này**. Cảnh báo ngoài 6 CWE đi vào A, nhưng ghi riêng là "C không có danh mục" |
| C3 | Bộ trích C chỉ hỗ trợ Java | Chỉ chọn repo Java |
| C4 | Semgrep CE không nối taint xuyên hàm, SARIF không có `codeFlows` | Bộ trích tự lần ngược. Đúng động cơ của C |
| C5 | Bán kính cửa sổ B (`--snippet-radius`, mặc định 10) ảnh hưởng mạnh (devlog 13/11: ±10 cho 6 `unknown`, ±25 cho 0) | Phải chỉnh trên `dev` và đưa vào manifest |
| C6 | **[Quyết định của người dùng]** Claude gán nhãn toàn bộ; người dùng kiểm tra một mẫu | Khoảng 10–12 giờ của người kiểm tra cho 50 cảnh báo. Proposal mục 10 cấm AI tạo nhãn đáp án nên phải sửa đề cương và báo nhóm |
| C7 | Claude (người gán nhãn) khác họ mô hình với model được đánh giá (DeepSeek) | Giảm thiên lệch tự khen, nhưng không loại bỏ được việc hai LLM cùng sai một kiểu. Ghi vào nguy cơ |
| C11 | **[Quyết định của người dùng]** Dùng model trong `.env`, là model cloud | Bỏ H2c (local so với cloud) |
| C8 | Không có quyền comment lên PR của người khác | RQ3 không đo được hành vi thật |
| C9 | Proposal: mã nguồn mở không được gọi là "công ty Z" | Đổi tên trong báo cáo |
| C10 | Test LLM chạy thật đang bị skip, `make check` trong repo có vấn đề nạp lại `.env` | Phải xử lý ở K2 |

## 4. Các hướng đã cân nhắc

| Hướng | Mô tả | Được | Mất |
|---|---|---|---|
| 1. Chỉ benchmark có đáp án | BenchmarkJava cho RQ2, Vul4J cho RQ4 | Không cần gán nhãn | Tỉ lệ cảnh báo sai nền cao, không phải luồng PR, mô hình có thể đã thuộc dữ liệu |
| 2. Chỉ PR thật mã nguồn mở | Replay PR lịch sử của 1–3 repo Java, nhóm tự gán nhãn | Sát proposal | Không có điểm kiểm chéo tự động, không có RQ4 |
| **3. Kết hợp** | Hướng 2 là dữ liệu chính. BenchmarkJava là phép kiểm có đáp án. Vul4J cho RQ4 | Có số liệu thật, có kiểm chéo | Vẫn tốn công gán nhãn |

**[Quyết định của người dùng]** chọn hướng 3.

---

## 5. Tiêu chí K: đánh giá mã nguồn chạy đúng/sai

### 5.1. Thế nào là đúng, thế nào là sai

Một ca **pass** khi kết quả quan sát khớp oracle viết **trước** khi chạy. Oracle không bao giờ là "LLM trả đúng nhãn": ở tầng mã, LLM được thay bằng Fake LLM, trừ ca smoke K2.3.

Mức độ lỗi theo test-plan mục 10.2:

| Mức | Ví dụ | Hệ quả với đánh giá R |
|---|---|---|
| **blocker** | Rò secret; thực thi mã PR; nói PR an toàn khi quét lỗi; chặn merge | Dừng mọi bước R |
| **major** | Mất cảnh báo thật trong pipeline; gộp trùng sai; dấu vân tay không ổn định; parser nhận đầu ra mơ hồ; phiếu gán nhãn lộ nhận định; số đo tính sai | Không được `freeze` cho tới khi sửa hoặc ghi giới hạn được chấp nhận |
| **minor** | Câu chữ comment, hiển thị | Không chặn |

Khi một cảnh báo bị "đánh giá sai", phải quy về đúng một thành phần:

| Loại lỗi | Định nghĩa | Ghi vào đâu |
|---|---|---|
| Scanner miss / scanner FP | Công cụ quét không báo / báo nhầm | RQ1 (đặc tính scanner), **không** phải lỗi bot |
| Normalize error | Gộp sai, đánh dấu mới/cũ sai | Lỗi mã (major) |
| Context miss | Bộ trích không tìm thấy source/sanitizer có thật, hoặc lấy nhầm hàm | Số đo chất lượng bộ trích (mục 5.6) |
| LLM verdict error | Đủ ngữ cảnh nhưng LLM kết luận sai | RQ2 |
| Policy/publish error | Thu gọn/hiển thị không đúng nhận định | Lỗi mã (major) |

### 5.2. Bước K1: rà soát truy vết (ca test ↔ test tự động)

**Việc:** lập bảng `test-plan ID → test pytest / hồ sơ E2E / chưa có`. Mỗi dòng có trạng thái đã chạy hay chưa và SHA lần chạy.

**Đầu ra:** `docs/test-records/<ngày>/results/traceability.md`.

**Cách làm [Đề xuất]:** đọc tên test trong `tests/` theo nhóm (`scan`, `normalize`, `context`, `llm`, `bot`, `app`, `evaluation`, `pipeline`, `store`), đối chiếu với SCN/NRM/CTX/LLM/BOT/FB/SEC/OPS/EVAL. Một ca chỉ được tính "có test" khi test đó khẳng định đúng oracle của ca, không chỉ cùng chủ đề.

**Pass:** 100% ca P0 có test tự động hoặc bằng chứng thủ công. Ca P1 thiếu thì ghi `not run` kèm lý do.

### 5.3. Bước K2: chạy bộ kiểm thử tự động

| Ca | Lệnh / cách chạy | Pass khi |
|---|---|---|
| K2.1 Tĩnh | `make check` (Ruff, format, MyPy) | Không lỗi |
| K2.2 Pytest cô lập | pytest với môi trường không nạp `.env` (khắc phục C10) | Toàn bộ pass. Mỗi ca skip có lý do ghi lại |
| K2.3 LLM smoke | `tests/llm/test_live.py` với model thật, cấu hình qua biến môi trường | Trả JSON hợp lệ theo schema trên các fixture đã có. **Không chấm nhãn** |
| K2.4 Đặc tả khác mã | LLM-09 (hai JSON object), LLM-07 (thiếu `finding_id`) | Nhóm chốt hành vi; mã và test sửa cùng lúc **trước** `freeze` |

### 5.4. Bước K3: ca bổ sung chưa có bằng chứng

Danh sách ưu tiên **[Đề xuất]**, lấy từ test-plan và các hồ sơ đã ghi:

| Ca | Vì sao quan trọng cho R | Oracle |
|---|---|---|
| NRM-05 + K3.a ổn định dấu vân tay | Dấu vân tay đổi thì pool bị đếm trùng, cảnh báo "mới" sai | Chèn dòng phía trên, đổi định dạng (commit chỉ reformat), đổi tên biến cục bộ: ghi kết quả thật. Lệch thì lập issue, **không** sửa oracle |
| NRM-01/02 trên SARIF có nhiều bộ luật | Thêm luật registry làm tăng ca trùng | Cùng CWE + file + hàm + sink chồng nhau thì gộp; khác CWE thì không |
| EVAL-xx phiếu mù | Phản mục tiêu số 2 | Grep phiếu xuất ra: không chứa `likely_*`, `variant`, `explanation`. Thứ tự xáo khác nhau giữa người gán |
| EVAL-xx khóa manifest | Phản mục tiêu số 1 | Đổi một byte prompt sau `freeze` thì `eval metrics --split eval` từ chối chạy |
| EVAL-xx số đo | Số đo sai thì kết luận sai | Tính tay trên bộ 10 cảnh báo giả: FP-removal, TP-loss, Wilson, McNemar, kappa khớp tới 3 chữ số |
| K3.b replay lặp lại | Cùng PR, cùng cấu hình | Hai lần replay cho cùng tập `finding_id`. Verdict giống nhau khi cache bật |
| BOT-07 PR từ fork thật | P1 | App không chạy mã PR, dùng `refs/pull/N/head` |
| OPS-03 restart giữa job | P1 | Không comment trùng |

### 5.5. Bước K4: chạy trên repo thật (độ bền và hiệu năng)

Chạy `pr-triage replay` trên các repo của mục 6.2, chế độ chỉ lưu, không đăng comment.

| Số đo | Cách đo | Ngưỡng đạt **[Đề xuất]** |
|---|---|---|
| Tỉ lệ run `ok` / `degraded` / `failed` | Đếm theo PR | `failed` ≤ 5%. Mỗi ca `failed` có nguyên nhân |
| Lỗi parser/scanner theo file | Log Semgrep, tree-sitter | Liệt kê. File lỗi nằm trong báo cáo độ phủ |
| Thời gian mỗi PR | Trung vị, p90: quét, trích, LLM, tổng | Trung vị tổng ≤ 15 phút (định nghĩa: từ lúc bắt đầu run tới khi có kết quả) |
| Token, chi phí mỗi PR | Từ `Verdict` | Ghi lại. Ngưỡng ngân sách do nhóm chốt |
| Tính tất định | Replay lại 10 PR | Tập `finding_id` trùng 100% |

### 5.6. Bước K5: chất lượng từng thành phần trên dữ liệu thật

Đo trên tập `dev` (không đo trên `eval` để khỏi rò rỉ):

| Thành phần | Số đo | Cách xác định |
|---|---|---|
| Bộ trích C | Tỉ lệ tìm thấy sink, tìm thấy source, có `missing`; số đoạn và độ dài bundle | Tự động |
| Bộ trích C | Độ chính xác source/sanitizer trên 30 bundle | Một người (không phải người viết bộ trích) đọc và chấm đúng/sai/thiếu |
| LLM | Tỉ lệ JSON hợp lệ, `invalid`, bằng chứng ngoài bundle | Tự động |
| Chuẩn hóa | Số cảnh báo bị gộp, số ca gộp nhầm trên 30 mẫu | Đọc tay |

**Quy tắc ADR 0003 D6:** nếu tỉ lệ bundle có `missing` trên `dev` > 50% **[Đề xuất ngưỡng]**, mở ADR xem xét Joern trước khi `freeze`.

### 5.8. Tùy chọn: chạy trong Jenkins (ba job tách quyền)

**[Quyết định của người dùng]** Thêm như phần tùy chọn của tiêu chí K. Làm sau bước 3 ở mục 8, không chặn đường chính RQ1/RQ2. Hiện repo chưa có Jenkinsfile; các lệnh CLI `run` / `publish` / `feedback` đã có.

| Ca | Cách làm | Pass khi |
|---|---|---|
| J1 CLI ba job (không cần Jenkins) | Chạy tuần tự `run` → `publish --post` → `feedback` trên một PR fork | Một comment; `publish` chạy được trong thư mục không có mã nguồn, chỉ có `triage-result.json` |
| J2 Dựng Jenkins | Jenkins LTS (Docker, local), Multibranch Pipeline + GitHub Branch Source trỏ tới repo fork; Jenkinsfile hai stage triage/publish chạy trong image `pr-triage` | PR mới tự kích hoạt pipeline |
| J3 Tách quyền | Credentials: khóa LLM chỉ ở stage triage; `GITHUB_TOKEN` (quyền comment) chỉ ở stage publish; publish không `checkout scm` | Kiểm tra log/biến môi trường từng stage: không lộ chéo |
| J4 Không chặn merge | Làm lỗi scanner/LLM có chủ đích | Build kết thúc không chặn (`catchError(buildResult: 'SUCCESS')`), comment "chưa quét xong" |
| J5 Base SHA | `git merge-base origin/$CHANGE_TARGET HEAD` | Cảnh báo mới khớp với kết quả GitHub App trên cùng PR |
| J6 Độ trễ CI | Thời gian stage triage + publish trên 5–10 PR fork (D4) | Ghi trung vị/p90. Đây là số đo "CI chậm thêm" cho RQ3; so với độ trễ của GitHub App trên cùng PR |

Cần kiểm tra trước: image có Semgrep không (`uv sync --no-dev`); SQLite dùng chung qua volume cố định trên agent, chạy tuần tự từng PR. Ước lượng 1–2 ngày, chưa thử.

### 5.7. Cổng vào trước khi chạy `eval`

Chỉ được chạy `eval freeze` khi đạt đủ:

- [ ] K2.1, K2.2 pass; K2.4 đã chốt và có test.
- [ ] Không còn blocker; mọi major đã sửa hoặc được ghi thành giới hạn có người chấp nhận.
- [ ] K3: ổn định dấu vân tay, phiếu mù, khóa manifest và số đo đều pass.
- [ ] K4: `failed` ≤ 5%, tính tất định 100%.
- [ ] K5 đã báo cáo; quyết định ADR 0003 D6 đã ghi.

---

## 6. Tiêu chí R: đánh giá kết quả nghiên cứu

### 6.1. Bốn bộ dữ liệu

| Mã | Dữ liệu | Dùng cho | Vai trò |
|---|---|---|---|
| **D1** | PR đã merge của 1–3 repo Java mã nguồn mở, bổ sung bằng quét nhánh chính nếu thiếu | RQ1, RQ2 (chính), mốc RQ3 | **Số liệu chính** |
| **D2** | Tập con OWASP BenchmarkJava, nhóm CWE trong C2 | Kiểm chéo RQ2 với đáp án có sẵn | Phụ, báo riêng |
| **D3** | Vul4J: các cặp bản lỗi/bản vá mà scanner báo được trên bản lỗi | RQ4 | Phụ |
| **D4** | PR do nhóm tự tạo trên fork của repo D1 | Minh họa RQ3 (độ trễ, chi phí, comment) | Chỉ mô tả |

### 6.2. Chọn repo cho D1

**Tiêu chí [Đề xuất]**, phải đạt tất cả:

1. Java, ứng dụng web hoặc dịch vụ có xử lý dữ liệu ngoài (servlet, Spring, JAX-RS), có SQL/JDBC/JPA.
2. ≥ 150 PR đã merge trong 3 năm gần nhất, đi qua review trên GitHub.
3. Giấy phép mã nguồn mở cho phép phân tích.
4. Quét thử nhánh chính được **≥ 1 cảnh báo / 1.000 dòng** trong nhóm CWE của C2 (đo ở bước pilot).
5. Không thuộc bộ dữ liệu đã biết dùng để huấn luyện/đánh giá lọc cảnh báo (BenchmarkJava, Juliet, WebGoat). Mục đích là giảm rủi ro mô hình đã thuộc đáp án.

**Ứng viên cần kiểm chứng** (chưa quét, chưa xác nhận có cảnh báo): Apache OFBiz, OpenMRS Core, DSpace. Chốt sau pilot.

**Tách repo [Đề xuất]:** nếu có ≥ 2 repo, giữ một repo **chỉ dùng cho `eval`** (proposal 7.3).

### 6.3. Cấu hình bộ quét

- **[Đề xuất]** 3 luật tùy chỉnh hiện có, cộng các luật Java trong Semgrep registry thuộc nhóm CWE của C2. Phiên bản Semgrep và mã băm bộ luật được khóa trong manifest. Đọc lại giấy phép bộ luật registry trước khi dùng.
- Không dùng CodeQL trên D1 (giữ nguyên thiết kế; có thể cân nhắc cho D3).
- Quét cả mã test nhưng gắn cờ `is_test_code`, báo riêng.

### 6.3a. Thay đổi sau pilot (2026-11-18, người dùng duyệt)

Pilot cho thấy replay PR không đủ dữ liệu: 60 PR/commit của OpenMRS, DSpace, OFBiz chỉ sinh 1 cảnh báo mới; nhánh chính của ba repo có tổng 70 cảnh báo (0,04–0,07 trên 1.000 dòng, ngưỡng 6.2.4 không repo nào đạt). Vì vậy, **thay mục 6.4 bên dưới** bằng:

1. **Nguồn cảnh báo:** quét 21 mốc lịch sử mỗi repo (commit first-parent cuối cùng trước ngày 18 của tháng 5 và 11, từ 11/2016 đến 11/2026), `pr-triage run --base none --variants none`, lấy hợp các cảnh báo duy nhất. Đây là **cảnh báo trên mã nguồn ở nhiều thời điểm, không phải cảnh báo trên PR**; báo cáo phải ghi rõ. Dữ liệu replay PR chỉ giữ cho phần mô tả RQ3 (độ trễ, chi phí).
2. **Repo:** thêm Apache Roller, Apache JSPWiki, OpenCms (Shopizer bị loại: nhánh chính 54 commit, 0 cảnh báo). Tổng 6 repo, **227 cảnh báo duy nhất**: DSpace 76, OFBiz 44, OpenMRS 43, Roller 24, OpenCms 24, JSPWiki 16.
3. **Tách tập theo nguyên repo, không theo thời gian** (khoảng 72% cảnh báo đã có từ mốc 2016 nên tách theo thời gian làm `eval` chỉ còn vài chục ca). Mỗi repo thuộc trọn một tập, đúng tinh thần proposal 7.3 "giữ một repo chỉ dùng cho `eval`":
   - **`eval`: DSpace, OpenMRS Core, Roller = 143 ca.**
   - **`dev`: OFBiz, OpenCms, JSPWiki = 84 ca.**
   - Thực hiện bằng `pr-triage eval pool --cutoff 9999-12-31T00:00:00Z --eval-only-repo DSpace --eval-only-repo openmrs-core --eval-only-repo roller` (mốc `cutoff` xa để mọi repo còn lại vào `dev`).
4. **Rủi ro cỡ mẫu:** `eval` chỉ dư 3 ca so với mức tối thiểu 140. Dấu vân tay chứa đường dẫn file nên một đoạn mã bị đổi tên/di chuyển file có thể bị đếm hai lần; khi gán nhãn, đánh dấu ca trùng (cột `code_ref`). Nếu sau khi loại trùng `eval` < 140, báo đúng cỡ mẫu thực tế, không nới tiêu chí, không đổi phân chia sau khi đã xem nhãn.
5. Tiêu chí 6.2.4 (mật độ ≥ 1/1.000 dòng) bị bỏ. Tiêu chí 6.2.2 (≥ 150 PR) không còn là điều kiện vì dữ liệu chính không lấy từ PR.

Ghi quyết định thành ADR 0016 (thay một phần D1 của ADR 0015).

### 6.4. Dựng pool và tách tập (bản gốc, đã được thay bởi 6.3a)

1. **Pilot (10–20 PR mỗi repo):** chạy replay, đo số cảnh báo mới mỗi PR, thời gian, chi phí. Từ đó tính số PR cần cho 200 cảnh báo.
2. **Replay đầy đủ:** 100–200 PR. Nếu pool < 200, quét thêm nhánh chính tại commit mốc. Ghi nguồn của từng cảnh báo (`pr` hoặc `main-scan`).
3. **Khử trùng lặp** bằng dấu vân tay; mỗi cảnh báo chỉ thuộc một tập.
4. **Tách theo thời gian:** PR merge trước mốc T vào `dev`, sau mốc T vào `eval`. Chọn T sao cho `dev` có ≥ 60 và `eval` có ≥ 140 cảnh báo. Repo dành riêng cho `eval` đi hết vào `eval`.
5. Nếu > 400 cảnh báo: lấy mẫu phân tầng theo luật/CWE, có trọng số mẫu (proposal 7.4).

Lệnh: `pr-triage replay` rồi `pr-triage eval pool`.

### 6.5. Gán nhãn: Claude gán, người kiểm tra mẫu

**[Quyết định của người dùng]** Claude là người gán nhãn chính (`labeler = ai-claude`, ghi model ID của phiên gán nhãn). Người dùng là người kiểm định (`labeler = human-1`).

| Bước | Quy tắc |
|---|---|
| Thứ tự chống rò rỉ | Với mỗi tập: dựng pool → xuất phiếu → **Claude gán nhãn xong** → `label-import` → mới chạy B/C trên tập đó. Claude không đọc bảng `Verdict`, `triage-result.json` hay comment của tập chưa gán xong |
| Phiếu | `pr-triage eval label-export`. Chỉ có cảnh báo, vị trí mã, tiêu chí Phụ lục B. Claude đọc mã nguồn tại commit tương ứng khi cần, không đọc output của bot |
| Hiệu chuẩn người gán nhãn AI (D2) | Trước khi gán D1, Claude gán mù 30 test case BenchmarkJava (nhóm CWE của C2) rồi so với đáp án có sẵn. Báo độ chính xác và kappa. Dưới 0,6 thì sửa tiêu chí theo CWE rồi thử lại trên 30 ca khác |
| Hiệu chuẩn tiêu chí (D1 `dev`) | Claude gán 30 cảnh báo đầu của `dev`; người dùng xem 10 ca để thống nhất cách hiểu Phụ lục B. Tiêu chí chi tiết theo CWE được chốt và ghi lại |
| `dev`, `eval` | Claude gán toàn bộ, mỗi nhãn có lý do một câu và vị trí mã căn cứ |
| Kiểm định bằng người | 50 cảnh báo `eval` lấy ngẫu nhiên, phân tầng theo CWE và theo nhãn của Claude. Người dùng gán **độc lập, không xem nhãn của Claude**, rồi mới so. Tính Cohen's kappa và bảng nhầm lẫn |
| Phân xử | Các ca bất đồng trong mẫu: người dùng quyết định nhãn cuối (người thắng). Ghi riêng tỉ lệ bất đồng theo CWE |
| Ngưỡng | Kappa ≥ 0,6: dùng nhãn Claude cho phần còn lại, báo là "nhãn tham chiếu AI, kiểm định trên n = 50". Kappa < 0,6: sửa tiêu chí trên `dev`, Claude gán lại `eval`, kiểm định lại trên 50 ca **mới**. Lần hai vẫn < 0,6: kết quả RQ1/RQ2 chỉ báo trên mẫu 50 ca có nhãn người, ghi "nhãn AI không đạt" |
| Độ nhạy | Tính lại số đo chính RQ2 trên riêng 50 ca nhãn người và so chiều với kết quả toàn tập |
| `uncertain` | Ca cần kiến thức dự án: tra issue/commit sửa sau đó nếu có, ghi nguồn; còn lại giữ `uncertain` |

### 6.6. Chỉnh trên `dev` rồi khóa

Chỉ trên `dev`, theo thứ tự:

1. Bán kính cửa sổ B: thử 10 / 25 / 40; chọn giá trị có TP-loss thấp nhất, hòa thì chọn số `unknown` ít hơn.
2. Prompt (chung cho B và C) và trần ngữ cảnh C.
3. Chọn cách hiển thị theo proposal 6.2 (≥ 50% FP-removal → TP-loss thấp nhất → rẻ hơn).
4. Chốt ngưỡng ở `configs/eval/thresholds.yml` và ngưỡng ra quyết định ở mục 6.9.
5. `pr-triage eval freeze` + tag Git `eval-freeze-1`.

### 6.7. Chạy `eval` và số đo

- Chạy A, B, C trên **toàn bộ** cảnh báo `eval`, cùng head/base, cùng model.
- Đo độ ổn định: chạy lại 3 lần, tắt cache, trên 50 cảnh báo ngẫu nhiên của `eval`. Báo tỉ lệ cảnh báo đổi nhãn.
- `pr-triage eval metrics --split eval` và `eval export`.

| RQ | Số đo | Cách tính |
|---|---|---|
| RQ1 | Tỉ lệ cảnh báo sai | `false / (true + false)` kèm Wilson; thêm biên khi mọi `uncertain` là true / là false |
| RQ1 | Mật độ | Cảnh báo mới / PR, theo luật và CWE |
| RQ2 | FP-removal, TP-loss | `F_c/F`, `T_c/T` cho B và C |
| RQ2 | Lượt đọc tiết kiệm / lỗi thật bị mất | `F_c/T_c`; thêm ngoại suy theo tỉ lệ nền 22%, 76%, 92% |
| RQ2 | B so với C | Bảng 2×2 theo cặp, McNemar, **báo số ca bất đồng** |
| RQ2 | Ổn định, `unknown`, chi phí, độ trễ | Như 5.5 |
| Độ nhạy | Bootstrap theo PR | Chỉ khi ≥ 10 PR có cảnh báo |

### 6.8. Phần phụ: D2, D3, D4

**D2 BenchmarkJava (kiểm chéo):**
- Lấy cùng nhóm CWE, cỡ 100–200 test case, nhãn là đáp án có sẵn (mức file), cấu hình đã khóa.
- Câu hỏi: thứ tự B và C trên D2 có cùng chiều với D1 không?
- Thêm câu thăm dò "Đây là test case nào của OWASP Benchmark?" để phát hiện mô hình đã thuộc dữ liệu.

**D3 Vul4J (RQ4):**
- Chỉ lấy cặp mà scanner báo trên bản lỗi; mục tiêu 30 cặp.
- Chấm: báo trên bản lỗi, im trên bản vá. Viết lại mô tả cho trung tính, bỏ mã CVE.
- Nếu < 30 cặp, báo đúng số có được. Không nới tiêu chí.
- Kendall τ so thứ tự cách giữa D1 và D3.

**D4 + mốc lịch sử (RQ3 rút gọn):**
- Mốc: tỉ lệ cảnh báo có ở commit đầu của PR nhưng biến mất ở bản merge, trên D1. Cần replay ở mức commit đầu của PR, không chỉ commit merge; đây là việc cần kiểm tra lệnh `replay` có hỗ trợ không.
- D4: 5–10 PR nhóm tạo trên fork, chạy GitHub App thật. Đo độ trễ webhook → comment, chi phí, ảnh comment.
- **Không** dùng D4 làm bằng chứng hành vi lập trình viên.

### 6.9. Quy tắc đọc kết quả (chốt trước `eval`)

| Giả thuyết | Kết luận "ủng hộ" khi | Kết luận "không ủng hộ" khi | Còn lại |
|---|---|---|---|
| H1: tỉ lệ cảnh báo sai < 76% | Cận trên Wilson < 76% | Cận dưới ≥ 76% | Chưa đủ bằng chứng |
| H2a: C mất ít lỗi thật hơn B | TP-loss(C) < TP-loss(B) và McNemar trên cảnh báo true có p < 0,05 | p ≥ 0,05 hoặc ngược chiều | Báo số ca bất đồng. Nếu < 10 thì ghi "mẫu quá nhỏ" |
| H2b: C loại cảnh báo sai không kém B | FP-removal(C) ≥ FP-removal(B) − 10 điểm **[Đề xuất biên]** | Kém hơn quá biên | — |
| "Đáng dùng" (proposal 7.9) | Cách được chọn đạt đủ: FP-removal ≥ 50%, TP-loss ≤ 10%, trung vị ≤ 15 phút, chi phí trong ngân sách | Trượt bất kỳ điều kiện nào | Điều kiện không đo được → "chưa đủ bằng chứng" |
| H2c (local so với cloud) | **Không làm**: chỉ có model cloud trong `.env` | | |

Diễn giải bắt buộc: kết quả là của **các repo mã nguồn mở đã chọn**, không khái quát cho doanh nghiệp.

### 6.10. Nguy cơ riêng của phương án mã nguồn mở

| Nguy cơ | Xử lý |
|---|---|
| Mô hình đã thấy mã nguồn mở khi huấn luyện | Tiêu chí 6.2.5. Báo thời điểm cắt dữ liệu của model. Câu thăm dò ở D2 |
| Nhãn do AI gán: hai LLM cùng sai một kiểu, làm số đo đẹp giả tạo | Hiệu chuẩn trên D2, kiểm định bằng người n = 50, phân tích độ nhạy trên phần nhãn người, báo rõ trong giới hạn |
| Người gán nhãn không hiểu dự án | Tra issue/commit sửa, giữ `uncertain` riêng |
| Mật độ cảnh báo thấp trên PR | Pilot trước, quét nhánh chính bù, báo nguồn `pr`/`main-scan` riêng |
| Bộ luật registry thay đổi | Khóa phiên bản trong manifest |

---

## 7. Đầu ra và nơi lưu

| Đầu ra | Nơi lưu |
|---|---|
| Hồ sơ K (traceability, kết quả chạy, issue) | `docs/test-records/<ngày>/` theo quy ước scenarios/results/testers |
| Runbook đợt đánh giá (lệnh, SHA, tham số) | `.docs/quality/evaluation/runbook-<ngày>.md` |
| Kết quả R tổng hợp | `.docs/quality/evaluation/results-<ngày>.md` |
| SARIF thô, phiếu nhãn có mã, DB | Ngoài repo, trong thư mục dữ liệu local. Không commit |
| Quyết định thay đổi (ví dụ đổi sang mã nguồn mở, Joern) | ADR mới trong `.docs/architecture/decisions/` |

Không ghi API key, webhook secret vào tài liệu.

## 8. Thứ tự thực hiện

| Bước | Việc | Phụ thuộc |
|---|---|---|
| 0 | Ghi ADR "đánh giá trên mã nguồn mở, nhãn tham chiếu AI có kiểm định người"; ghi chú lệch proposal mục 8.3 và mục 10 (người dùng báo nhóm) | — |
| 1 | K1 rà soát truy vết, K2 chạy bộ tự động, chốt K2.4 | — |
| 2 | Chọn repo: quét thử nhánh chính 3 ứng viên, pilot 10–20 PR (chỉ quét, chưa chạy LLM trên cảnh báo sẽ vào pool) | 1 |
| 3 | K3 ca bổ sung, K4 replay đầy đủ ở chế độ chỉ quét (A) | 2 |
| 4 | Hiệu chuẩn Claude trên 30 ca D2; dựng pool, tách tập | 3 |
| 5 | Claude gán nhãn `dev` → chạy B/C trên `dev` → K5, chỉnh trên `dev` | 4 |
| 6 | Cổng 5.7 → `freeze` + tag | 5 |
| 7 | Claude gán nhãn toàn bộ `eval`; xuất mẫu kiểm định 50 ca cho người dùng | 6 |
| 8 | **Sau bước 7:** chạy B/C trên `eval`, đo ổn định; D2, D3, D4. Người dùng kiểm định song song | 7 |
| 9 | Tính kappa, số đo, độ nhạy, đọc theo 6.9, viết kết quả | 8 |
| J (tùy chọn) | Mục 5.8: J1 → J6 | 3 |

## 9. Để lại cho người thực hiện

- Tên test cụ thể ứng với từng ca ID (xác định ở K1).
- Danh sách luật registry cụ thể, sau khi đọc giấy phép.
- Mốc thời gian T để tách tập (sau pilot).
- Cách cài môi trường pytest không nạp `.env`.
- Kiểm tra `replay` có chạy được ở commit đầu của PR không; nếu không, ghi thành việc cần thêm vào mã.
- Kiểm tra `replay` có chế độ chỉ quét (không gọi LLM) để gán nhãn trước khi chạy B/C; nếu không, thêm cờ hoặc tách bước. Đây là điều kiện của thứ tự chống rò rỉ ở mục 6.5.

## 10. Lựa chọn của người thiết kế cần anh/chị xem lại

1. Phạm vi CWE là 6 CWE injection có trong danh mục (C2).
2. Thêm luật Semgrep registry để đủ cảnh báo.
3. Ngưỡng `failed` ≤ 5%, `missing` > 50% thì xem xét Joern, biên không-kém-hơn 10 điểm cho H2b.
4. Ba repo ứng viên ở 6.2.
5. Bán kính B thử 10/25/40.
6. RQ3 rút gọn thành mốc lịch sử và D4 mô tả.
7. Mẫu kiểm định 50 ca phân tầng; người dùng thắng khi bất đồng; quy tắc lùi khi kappa < 0,6 (mục 6.5).
8. Hiệu chuẩn Claude trên 30 ca BenchmarkJava trước khi gán D1.

## 11. Cần người dùng làm

- Kiểm định độc lập 50 cảnh báo `eval` (khoảng 10–12 giờ) và xem 10 ca hiệu chuẩn `dev`.
- Báo nhóm (và thầy nếu cần) về hai thay đổi đề cương: dùng mã nguồn mở thay công ty Z; nhãn tham chiếu do AI gán thay cho hai người gán.
