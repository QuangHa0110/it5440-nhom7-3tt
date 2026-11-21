# Quy ước chung

**Quy ước chung của Nhóm 7 cho đề tài 3TT**

| | |
|---|---|
| Phiên bản | 0.1, bản nháp để cả nhóm góp ý |
| Hạn chốt | 09/11/2026 cho mục 2–5 và 11–13; các mục khác theo mục 14 |
| Áp dụng cho | Toàn bộ thành viên và các công cụ AI họ dùng |

## 1. Cách dùng tài liệu

Tài liệu này giúp 7 người làm song song mà vẫn ghép được với nhau. Khi đã chốt, mọi thay đổi phải qua pull request, được người giữ mục đó đồng ý và báo cho cả nhóm.

Các tên trường, danh sách và con số dưới đây là đề xuất ban đầu. Nhóm được sửa trước khi chốt.

## 2. Thuật ngữ thống nhất

| Từ dùng trong nhóm | Từ dùng trong code | Nghĩa |
|---|---|---|
| Bài | `case` | Một pull request trong bộ dữ liệu, gồm một cặp `base` và `head` |
| Cảnh báo | `finding` | Kết quả của công cụ quét, đã chuẩn hóa |
| Báo cáo | `report` | Kết quả cuối của một cách A, B, C hoặc D |
| Cách | `method` | Một trong bốn cách A, B, C, D |
| Đáp án | `ground_truth` | Thông tin lỗi thật của một bài |
| Lần chạy | `repeat` | Lần lặp của cùng một cấu hình |

## 3. Định dạng dữ liệu

Dữ liệu dùng JSON, mã hóa UTF-8. Tên trường viết tiếng Anh theo kiểu `snake_case`.

Quy tắc chung:

- Đường dẫn file luôn tương đối theo gốc repo và dùng dấu `/`.
- Số dòng đếm từ 1.
- Thời gian dùng định dạng ISO 8601, múi giờ UTC.
- Trường chưa có giá trị ghi `null`, không bỏ trường.
- Mỗi file có `schema_version`.

### 3.1. Bài

File `dataset/cases.json`. File này không chứa thông tin lộ đáp án.

```json
{
  "schema_version": "0.1",
  "case_id": "c-0001",
  "repo_url": "https://github.com/example/project",
  "base": "<commit>",
  "head": "<commit>",
  "kind": "vulnerable",
  "split": "dev",
  "builds": true
}
```

`kind` nhận `vulnerable`, `fixed` hoặc `normal`. `split` nhận `dev` hoặc `eval`.

### 3.2. Cảnh báo

Mỗi cảnh báo đã chuẩn hóa có dạng:

```json
{
  "schema_version": "0.1",
  "finding_id": "f-000123",
  "case_id": "c-0001",
  "commit": "<commit>",
  "tool": "semgrep",
  "rule_id": "java.lang.security.audit.sqli",
  "cwe": "CWE-89",
  "tool_severity": "high",
  "file": "src/main/java/app/UserController.java",
  "function": "getUser",
  "start_line": 42,
  "end_line": 44,
  "fingerprint": "a3f91c02d4e7"
}
```

### 3.3. Báo cáo

Mọi cách đều xuất cùng một định dạng, kể cả cách A:

```json
{
  "schema_version": "0.1",
  "report_id": "r-000045",
  "case_id": "c-0001",
  "method": "D",
  "repeat": 1,
  "sources": ["semgrep", "agent"],
  "cwe": "CWE-89",
  "severity": "critical",
  "priority_score": 65,
  "file": "src/main/java/app/UserController.java",
  "function": "getUser",
  "start_line": 42,
  "end_line": 44,
  "fingerprint": "a3f91c02d4e7",
  "verdict": "likely_real",
  "reason": "id lấy từ request và ghép thẳng vào câu SQL",
  "suggestion": "Dùng PreparedStatement",
  "confidence": 0.9
}
```

`severity` nhận `critical`, `high`, `medium` hoặc `low`. `verdict` nhận `likely_real`, `likely_false` hoặc `unknown`; cách A luôn ghi `unknown`. `reason`, `suggestion` và `confidence` của cách A ghi `null`.

### 3.4. Kết quả trả về của LLM và agent

LLM và agent chỉ được trả về JSON theo dạng dưới đây. Mức độ, điểm ưu tiên và dấu vân tay do script tính.

```json
{
  "findings": [
    {
      "cwe": "CWE-89",
      "file": "src/main/java/app/UserController.java",
      "function": "getUser",
      "start_line": 42,
      "end_line": 44,
      "verdict": "likely_real",
      "reason": "...",
      "suggestion": "...",
      "confidence": 0.9
    }
  ]
}
```

Script loại kết quả và ghi log nếu JSON sai dạng, file hoặc dòng không tồn tại, hoặc CWE không hợp lệ.

### 3.5. Đáp án

Đáp án được lưu ngoài repo trong suốt quá trình chạy và chấm, và chỉ công khai sau khi có kết quả cuối.

```json
{
  "schema_version": "0.1",
  "case_id": "c-0001",
  "cve": "CVE-YYYY-NNNNN",
  "cwe": "CWE-89",
  "files": ["src/main/java/app/UserController.java"],
  "functions": ["getUser"],
  "root_cause": "Mô tả ngắn nguyên nhân",
  "source": "Vul4J"
}
```

### 3.6. Thông tin lần chạy

Mỗi lần chạy ghi một file `run.json`:

```json
{
  "schema_version": "0.1",
  "run_id": "2026-11-20-a1b2c3d",
  "code_commit": "<commit>",
  "experiment_config": "experiment.yaml",
  "started_at": "2026-11-20T02:00:00Z",
  "duration_seconds": 412,
  "input_tokens": 12000,
  "output_tokens": 900,
  "cost_usd": 0.12,
  "tools_ran": ["semgrep", "spotbugs"],
  "tools_failed": []
}
```

## 4. Giao diện chương trình

Mỗi lệnh chạy độc lập, chỉ đọc và ghi file theo định dạng chung. Phần chưa xong được thay bằng file mẫu trong `tests/fixtures/`.

| Lệnh | Đầu vào | Đầu ra |
|---|---|---|
| `python -m core.scan` | `--case`, `--commit` | Kết quả gốc của công cụ |
| `python -m core.normalize` | Kết quả gốc | `findings.json` |
| `python -m core.dedup` | Cảnh báo của `base` và `head` | `new_findings.json` |
| `python -m core.review` | `--case`, `--method`, `--repeat` | `reports.json`, `run.json` |
| `python -m core.evaluate` | `--run`, `--ground-truth` | `metrics.json` |
| `python -m core.comment` | `reports.json`, số pull request | Comment trên pull request |

Quy tắc:

- Mã thoát 0: chạy xong. Mã 1: lỗi đầu vào. Mã 2: một phần không chạy được, kết quả vẫn dùng được và ghi trong `run.json`.
- Log ghi vào stderr, không trộn vào file kết quả.
- Mọi tham số bí mật lấy từ biến môi trường, không đưa lên dòng lệnh.

Kết quả chạy lưu theo đường dẫn:

```tree
results/raw/<run_id>/<case_id>/<method>/<repeat>/
```

Thư mục `results/raw/` đã nằm trong `.gitignore`.

## 5. Cấu trúc repo

```tree
core/           Chương trình lõi, định dạng dữ liệu, dấu vân tay
pipeline/       Jenkinsfile, Dockerfile, script chạy công cụ
llm/            Prompt, script gọi LLM và agent
rules/          Luật Semgrep tùy biến
dataset/        Danh sách bài, không có đáp án
analysis/       Thống kê, bảng, biểu đồ
tests/          Kiểm thử và file mẫu
results/        Số liệu đã tổng hợp và ẩn danh
paper/          Báo cáo
slides/         Slide
docs/           Tài liệu
```

Mỗi phần chỉ sửa thư mục của mình. Khi cần sửa `core/schema` hay các hàm dùng chung, phải báo người giữ mục đó.

| Phần | Thư mục chính |
|---|---|
| 1. Bài có lỗi | `dataset/` |
| 2. Đối chứng và tổng quan | `dataset/`, `paper/` |
| 3. Lõi và cách A | `core/` |
| 4. Cách B | `llm/` |
| 5. Cách C và D | `llm/` |
| 6. Đánh giá và thống kê | `analysis/` |
| 7. Jenkins, comment và demo | `pipeline/` |

## 6. Dấu vân tay và so khớp

Chỉ dùng một bản cài đặt trong `core/fingerprint.py`. Không phần nào tự viết lại.

**Dấu vân tay của cảnh báo** dùng để biết cảnh báo có mới không:

1. Lấy đoạn mã tại vị trí cảnh báo.
2. Bỏ khoảng trắng thừa và chú thích.
3. Ghép đường dẫn file, tên hàm, `rule_id` và đoạn mã đã chuẩn hóa.
4. Tính SHA-256 và lấy 12 ký tự đầu.

Không dùng số dòng. Đổi tên file sẽ tạo dấu vân tay mới, và nhóm chấp nhận giới hạn này.

**So khớp giữa các nguồn:** hai kết quả được coi là trùng nếu cùng file, cùng hàm và cùng họ CWE ở mục 7. Hàm không xác định được thì so theo khoảng dòng, chênh lệch không quá 5 dòng.

## 7. Danh mục chuẩn

### 7.1. CWE

Danh sách cuối phụ thuộc số CVE có được và được chốt trước khi lấy dữ liệu.

| CWE | Tên | Họ | Mức độ |
|---|---|---|---|
| CWE-89 | SQL Injection | `injection` | Critical |
| CWE-78 | Command Injection | `injection` | Critical |
| CWE-502 | Deserialization | `deserialization` | Critical |
| CWE-22 | Path Traversal | `path` | High |
| CWE-611 | XXE | `xxe` | High |
| CWE-918 | SSRF | `ssrf` | High |
| CWE-79 | XSS | `xss` | Medium |
| CWE-798 | Secret trong mã | `credential` | High |

CWE ngoài danh sách thuộc họ `other`, mức Medium. Báo cáo loại này vẫn được giữ nhưng tính riêng trong thống kê.

### 7.2. Điểm ưu tiên

Mức độ quyết định nhóm. Điểm ưu tiên sắp xếp trong cùng một mức.

| Yếu tố | Điểm |
|---|---|
| Critical, High, Medium, Low | 40, 30, 20, 10 |
| Mỗi nguồn cùng báo, từ nguồn thứ hai | +5 |
| Có gọi API nguy hiểm | +10 |
| Dữ liệu có thể đi từ ngoài vào | +10 |
| Nằm trong mã test | Hạ một mức |

Mã test ở mức Low vẫn giữ mức Low.

### 7.3. Phạm vi loại trừ

- Bỏ qua: `target/`, `build/`, `.gradle/`, `generated-sources/`, `generated/`.
- Bỏ qua file lớn hơn 1 MB.
- Mã test là `src/test/`.
- Mọi danh sách để trong `core/config/`, không viết cứng trong code.

## 8. Quy tắc chấm

### 8.1. Tìm thấy lỗi

Một báo cáo **tìm thấy lỗi** khi thỏa cả ba điều kiện:

1. Chỉ đúng file trong đáp án.
2. Chỉ đúng hàm liên quan, hoặc đúng đoạn mã thuộc luồng lỗi.
3. Mô tả đúng nguyên nhân, không chỉ trùng CWE.

### 8.2. Nhãn cho báo cáo ngoài đáp án

| Nhãn | Khi nào dùng |
|---|---|
| Đúng | Có thể chỉ ra dữ liệu xấu đi tới vị trí nguy hiểm mà không được kiểm soát |
| Sai | Có bằng chứng dữ liệu được kiểm soát, không thể tới được, hoặc mã không hoạt động như báo cáo nói |
| Không chắc | Sau 10 phút vẫn không đủ thông tin kết luận |

Mỗi nhãn kèm một câu lý do. Nhóm bổ sung 3–5 ví dụ cho từng CWE trước khi chấm.

### 8.3. Quy trình

1. Người chấm chỉ thấy pull request và nội dung báo cáo, không thấy `method`, `sources`, `verdict` và `confidence`.
2. Hai người chấm độc lập trên công cụ chấm, không trao đổi trước khi xong.
3. Tính Cohen's kappa. Dưới 0.6 thì dừng, sửa tiêu chí và chấm lại trên một mẫu mới.
4. Bất đồng được hai người thảo luận. Nếu vẫn khác nhau, người thứ ba quyết định.
5. Không dùng AI để quyết định nhãn hoặc đáp án.

Thành viên phần 4 và 5 không chấm. Đáp án chỉ được mở sau khi người chấm đã xong báo cáo.

## 9. Bộ dữ liệu

- Điều kiện chọn bài được viết trước khi lấy dữ liệu.
- Ghi lại mọi trường hợp bị loại kèm lý do.
- Chia `dev` và `eval` theo dự án: một dự án chỉ nằm ở một phần. Đề xuất 30% `dev`, 70% `eval`.
- Xóa khỏi bài thay đổi trong test, nội dung commit, mã CVE và chú thích lộ đáp án.
- Không mở pull request hay comment lên repo gốc.
- Chỉ dùng secret giả.
- Sau khi khóa `eval`, chỉ sửa khi có lỗi rõ ràng, và phải ghi lại.

## 10. Quy tắc thí nghiệm

Mọi cấu hình nằm trong `experiment.yaml`:

```yaml
schema_version: "0.1"
model:
  cloud: "<tên-mô-hình>"
  local: "<tên-mô-hình>"
agent:
  name: "<tên-agent>"
  version: "<phiên-bản>"
tools:
  semgrep: "<phiên-bản>"
  spotbugs: "<phiên-bản>"
  findsecbugs: "<phiên-bản>"
repeats: 3
limits:
  timeout_seconds_per_case: 900
  max_cost_usd_per_case: 1.0
network: "disabled"
```

Các con số giới hạn là đề xuất ban đầu và sẽ chỉnh sau khi đo trên phần `dev`.

- Chỉ chỉnh prompt và cấu hình trên phần `dev`.
- Trước khi chạy `eval`, gắn thẻ Git, ví dụ `experiment-v1`, và không chỉnh prompt sau đó.
- B, C và D dùng cùng một mô hình cloud.
- Kết quả không có `run.json` thì không được dùng trong báo cáo.

## 11. Quy tắc Git

- Không commit trực tiếp vào `main`.
- Tên nhánh theo dạng `<phan>/<viec>`, ví dụ `core/dedup`, `llm/prompt-b`.
- Mỗi pull request làm một việc, cần một người review và qua kiểm thử.
- Nội dung commit viết ngắn gọn bằng tiếng Việt, bắt đầu bằng động từ.
- Không force push lên nhánh dùng chung.
- Tạo issue cho mỗi việc, có người nhận và hạn.

## 12. Quy tắc dùng AI

Mọi thành viên được dùng AI. Nội dung cần đưa vào `AGENTS.md` ở gốc repo:

- Python 3.11 trở lên, định dạng dữ liệu theo mục 3, giao diện theo mục 4.
- Mọi hàm xử lý dữ liệu có kiểm thử và file mẫu.
- Không tự đổi định dạng dữ liệu hay giao diện.
- Không tạo đáp án, không gán nhãn.
- Không commit secret hoặc kết quả thô.

Trách nhiệm của người dùng AI:

- Đọc và hiểu mọi thứ mình merge. Khi bảo vệ, mỗi người phải giải thích được phần của mình.
- Tự kiểm tra trích dẫn, số liệu và tên bài báo, vì AI có thể tạo ra thông tin không có thật.
- Lưu prompt chính trong `docs/ai-log/`, để nhóm trình bày được cách đã dùng AI.
- Không đưa secret hay dữ liệu nhạy cảm vào công cụ AI.

Công cụ AI dùng để viết code không phải là đối tượng thí nghiệm. Chỉ cấu hình trong `experiment.yaml` mới được tính là kết quả.

Quy định của môn học về việc dùng AI cần hỏi lại thầy trước khi chốt mục này.

## 13. Quy tắc an toàn cho repo public

Không commit:

- Tên công ty, tên dự án nội bộ, mã nguồn hay đường dẫn nội bộ.
- Secret, token, file `.env`.
- Kết quả quét thô, PDF bài báo, danh sách học viên.
- Đáp án, trước khi có kết quả cuối.

Nếu phát hiện lỗi thật chưa công bố trong dự án mã nguồn mở, không ghi lên repo public. Báo trưởng nhóm để gửi riêng cho maintainer theo chính sách bảo mật của dự án.

## 14. Người giữ và hạn chốt

| Mục | Người giữ | Hạn |
|---|---|---|
| 2, 3, 4, 6 Dữ liệu, giao diện, dấu vân tay | Phần 3 | 09/11 |
| 5, 11, 13 Repo, Git, an toàn | Trưởng nhóm | 09/11 |
| 12 Dùng AI | Trưởng nhóm | 09/11 |
| 7, 9 Danh mục và bộ dữ liệu | Phần 1 | 12/11 |
| 8 Quy tắc chấm | Phần 6 | 15/11 |
| 10 Thí nghiệm | Phần 6 | 17/11 |

Việc cần làm ngay:

1. Cả nhóm đọc và góp ý trước 09/11.
2. Phần 3 đưa định dạng dữ liệu thành JSON Schema và file mẫu trong `tests/fixtures/`.
3. Trưởng nhóm tạo `AGENTS.md` và các issue đầu tiên.
4. Mỗi phần chạy thử lệnh của mình trên file mẫu.
