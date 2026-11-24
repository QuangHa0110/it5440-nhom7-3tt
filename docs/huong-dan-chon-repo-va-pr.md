# Hướng dẫn chọn repo và pull request để chạy thực nghiệm

Tài liệu cho từng thành viên tự tìm repo và PR, chạy ba cách A, B, C, rồi gộp dữ liệu để đo và kết luận. Dùng khi chưa chạy được trên mã của công ty (phương án dự phòng, proposal mục 8.3).

> **Trạng thái:** bản nháp cho nhóm góp ý. Việc đổi phạm vi sang repo cá nhân và mã nguồn mở cần được ghi thành ADR trước khi chạy tập `eval`.

## 1. Mục tiêu và chỉ tiêu

Mỗi PR được chạy cả ba cách trong một lượt:

- **A**: Semgrep `p/default` báo các cảnh báo **mới** của PR (head trừ base).
- **B**: LLM gắn nhãn từng cảnh báo của A, chỉ nhìn vài dòng mã quanh vị trí báo.
- **C**: như B, thêm ngữ cảnh luồng dữ liệu (nguồn, sink, hàm làm sạch, hàm gọi và được gọi).

B và C xét **cùng một tập cảnh báo** của A, nên so sánh được theo cặp. PR không có cảnh báo mới ở A thì không đóng góp dữ liệu.

**Chỉ tiêu mỗi thành viên:**

| | Tối thiểu | Nên đạt |
|---|---|---|
| PR có ít nhất 1 cảnh báo mới | 5 | 8–10 |
| Cảnh báo mới (cộng các PR) | 20 | 30 trở lên |
| Repo | 1 | 2 (để chia `dev` và `eval` theo repo nếu cần) |

Lý do đặt chỉ tiêu theo cảnh báo: kết luận "loại nhầm không quá 10% lỗi thật" chỉ đáng tin khi có khoảng 30 lỗi thật trở lên trong cả nhóm. Với 15 lỗi thật, kể cả không mất lỗi nào, cận trên khoảng tin cậy vẫn khoảng 20%.

## 2. Tiêu chí chọn repo

### Bắt buộc

| # | Tiêu chí | Vì sao |
|---|---|---|
| R1 | **Java** là ngôn ngữ chính, hoặc có phần Java đáng kể | Cách C chỉ có danh mục sink cho Java (`configs/context/java.yml`). Repo ngôn ngữ khác chỉ so được A và B |
| R2 | **Được phép gửi mã lên LLM**: mã nguồn mở có giấy phép công khai, hoặc repo cá nhân do chính mình sở hữu | Mã được gửi lên dịch vụ LLM. Không dùng mã của công ty nơi mình làm, kể cả phần viết trong giờ làm |
| R3 | **Có lịch sử PR hoặc commit thật**, lấy được base và head | Pipeline cần hai phiên bản để tính cảnh báo mới |
| R4 | **Ứng dụng nhận đầu vào từ bên ngoài**: web, REST API, CLI đọc file, truy vấn cơ sở dữ liệu, gọi lệnh hệ thống | Thư viện thuần tính toán hầu như không sinh cảnh báo injection |
| R5 | **Clone và đọc được mã** (không cần build) | Semgrep và bộ trích ngữ cảnh chỉ đọc mã nguồn |

### Nên có

| # | Tiêu chí | Vì sao |
|---|---|---|
| R6 | **Ít nổi tiếng**: dưới khoảng 1.000 sao, hoặc repo cá nhân | Repo lớn có thể đã nằm trong dữ liệu huấn luyện, làm LLM "nhớ" thay vì suy luận |
| R7 | **Bạn hiểu mã**, hoặc đọc được trong thời gian ngắn | Giúp gán nhãn đúng |
| R8 | Có hoạt động gần đây (commit trong 1–2 năm) | Có đủ PR mới cho tập `eval` theo thời gian |
| R9 | Kích thước vừa phải (khoảng 5.000–200.000 dòng Java) | Quá nhỏ thì ít cảnh báo, quá lớn thì quét chậm |

### Loại trừ

- **Repo đã dùng ở đợt trước:** DSpace, openmrs-core, roller, ofbiz-framework, opencms-core, jspwiki.
- **Repo benchmark hoặc cố tình chứa lỗi:** BenchmarkJava, WebGoat, Juliet, bộ lỗi gieo của nhóm. Các repo này đo việc khác và chỉ báo cáo riêng.
- **Fork không có thay đổi riêng**, repo chỉ có mã sinh tự động, repo bài tập sao chép.
- **Repo chứa secret thật hoặc dữ liệu cá nhân của người khác**, kể cả trong lịch sử commit.
- **Trùng repo với thành viên khác:** đăng ký trước ở bảng mục 5.

### Gợi ý nơi tìm repo mã nguồn mở

- Tìm trên GitHub với bộ lọc: `language:Java stars:50..1000 pushed:>2025-01-01` kèm từ khóa như `spring boot`, `servlet`, `jdbc`, `rest api`, `cms`, `admin`, `shop`, `forum`.
- Ứng dụng quản lý, CMS nhỏ, hệ thống đặt chỗ, bán hàng, diễn đàn, công cụ nội bộ mã nguồn mở thường có nhiều đường đi từ request tới SQL, file và lệnh hệ thống.
- Repo cá nhân: đồ án môn học, dự án phụ, mã viết bằng trợ lý AI ("vibe coding") đều hợp lệ nếu thỏa R1–R5.

## 3. Tiêu chí chọn pull request

| # | Tiêu chí | Ghi chú |
|---|---|---|
| P1 | **Có ít nhất 1 cảnh báo mới từ A** | Lọc bằng cách chạy A trước (mục 4, bước 3). Đây là tiêu chí quan trọng nhất |
| P2 | Đã merge, hoặc là một cặp commit trước và sau rõ ràng | Repo cá nhân không có PR thì một commit trên nhánh chính được coi là một "PR" (`replay` tự làm việc này) |
| P3 | Thay đổi mã Java thật | Bỏ PR chỉ sửa tài liệu, đổi phiên bản thư viện, định dạng lại mã, đổi tên hàng loạt |
| P4 | Kích thước vừa phải (dưới khoảng 1.000 dòng thay đổi) | PR khổng lồ khó gán nhãn và tốn token |
| P5 | Ghi lại **ngày merge** | Để chia `dev` (PR cũ) và `eval` (PR mới) theo thời gian |
| P6 | Không chọn PR theo kết quả B hoặc C | Chỉ được lọc theo A. Chọn PR vì "LLM làm tốt" làm sai lệch số liệu |

Không cần PR có lỗi bảo mật thật. Cảnh báo sai cũng là dữ liệu cần thiết: chính chúng là thứ B và C phải loại.

## 4. Quy trình cho mỗi thành viên

### Bước 1. Chuẩn bị môi trường (một lần)

```bash
git switch main && git pull
make setup
uv run python scripts/fetch_semgrep_rules.py --frozen   # tải p/default, kiểm mã băm với configs/semgrep/rulesets.lock
cp .env.example .env                                     # điền PR_TRIAGE_LLM_* do nhóm cấp; không commit .env
```

Nếu dùng dịch vụ LLM không chạy trên máy mình, đặt `PR_TRIAGE_LLM_ALLOW_EXTERNAL=1`. Chỉ làm vậy với mã thỏa R2.

### Bước 2. Lấy repo về chỗ không commit

```bash
git clone <url-repo> data/raw/<ma-repo>
```

`<ma-repo>` là tên ngắn không dấu, ví dụ `ha-shop`. `data/raw/` nằm trong `.gitignore`.

### Bước 3. Lọc PR bằng cách A (không gọi LLM, miễn phí)

Chạy trên nhiều commit gần đây, giữ lại các PR có cảnh báo mới:

```bash
uv run pr-triage replay --repo data/raw/<ma-repo> --repo-alias <ma-repo> \
  --count 40 --variants none --no-secrets \
  --db data/raw/<ma-repo>-a.sqlite --out data/raw/<ma-repo>-a
```

Mỗi commit sinh một file `replay-<sha>-merged.json`. Tóm tắt thành bảng, cột `A_moi` là số cảnh báo mới:

```bash
uv run python scripts/summarize_runs.py data/raw/<ma-repo>-a/replay-*.json > data/raw/<ma-repo>-loc-a.tsv
```

Chọn các PR có `A_moi` lớn hơn 0 và thỏa P2–P5. SHA base và head của từng commit nằm trong `result.run` của file JSON. Nếu 40 commit chưa đủ 5 PR, tăng `--count`. Nếu vẫn quá ít, đổi repo.

### Bước 4. Đăng ký repo và PR

Điền bảng ở mục 5 trước khi chạy B và C. Đăng ký xong thì không đổi danh sách PR theo kết quả của LLM (P6).

### Bước 5. Chạy đủ A, B, C trên các PR đã chọn

Cho từng PR đã chọn (base và head lấy từ bước 3):

```bash
uv run pr-triage run --repo data/raw/<ma-repo> --repo-alias <ma-repo> \
  --base <sha-base> --head <sha-head> --pr <so-pr> \
  --variants B,C --no-secrets \
  --db data/team/store.sqlite --out data/raw/<ma-repo>-run/<so-pr>
```

Cả nhóm dùng **cùng các tham số** đã chốt (`--snippet-radius`, `--display`, mô hình LLM, phiên bản luật). Tham số chốt sẽ ghi trong `configs/eval/` và khóa bằng tag `eval-freeze-<n>` trước khi chạy tập `eval`. Không tự chỉnh prompt hay tham số trên máy mình.

### Bước 6. Thu tư liệu

Làm theo mục 7 ngay sau khi chạy, khi kết quả còn trên màn hình.

### Bước 7. Nộp kết quả

Nộp file SQLite, thư mục kết quả và thư mục tư liệu cho người tổng hợp qua kênh riêng của nhóm, **không qua Git**. Người tổng hợp chạy `pr-triage eval pool`, xuất phiếu gán nhãn và tính số đo.

## 5. Bảng đăng ký

Giữ bảng ở nơi chung của nhóm (không commit tên repo cá nhân nếu chủ repo không muốn công khai). Mỗi PR một dòng:

| Thành viên | Mã repo | Nguồn (OSS / cá nhân) | Giấy phép | Ngôn ngữ | Số PR hoặc SHA merge | SHA base | SHA head | Ngày merge | Số cảnh báo A |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

## 6. Gán nhãn

- Nhãn kỹ thuật: **Thật**, **Sai**, **Không xác định**, theo Phụ lục B của proposal.
- **Không dùng AI để gán nhãn đáp án** (proposal mục 10).
- **Gán chéo và mù:** phiếu từ `eval label-export` không cho biết B hay C giữ hay loại cảnh báo. Mỗi cảnh báo trong tập `eval` cần hai người gán độc lập. Chủ repo có thể là một trong hai người vì hiểu mã, nhưng không phải người duy nhất.
- Người viết prompt và bộ trích ngữ cảnh không gán nhãn.
- Kappa dưới 0,6 thì dừng, sửa tiêu chí, rồi gán tiếp.

## 7. Tư liệu cho báo cáo và slide

Mỗi thành viên giữ tư liệu trong `data/raw/<ma-repo>-tulieu/`. Người tổng hợp chọn và làm sạch những gì đưa vào báo cáo (mục 7.4).

### 7.1. Số liệu bắt buộc

| Tệp | Cách tạo | Dùng cho |
|---|---|---|
| `loc-a.tsv` | Bảng lọc ở bước 3: bao nhiêu commit được quét, bao nhiêu có cảnh báo mới | Mô tả tập dữ liệu, mật độ cảnh báo |
| `ket-qua.tsv` | `uv run python scripts/summarize_runs.py data/raw/<ma-repo>-run/*/triage-result.json` | Bảng mỗi PR: số cảnh báo A, nhãn B và C, thời gian, token, chi phí |
| `thong-tin-repo.md` | Viết tay: nguồn, giấy phép, ngôn ngữ, số dòng Java, số sao, lý do chọn | Mục mô tả dữ liệu trong báo cáo |
| `nhat-ky.md` | Viết tay: ngày chạy, mô hình LLM, phiên bản luật, lỗi gặp phải, lần chạy lại | Phần giới hạn và tái lập |

### 7.2. Ảnh chụp

Đặt tên `<ma-repo>-pr<so>-<loai>.png`, ví dụ `ha-shop-pr12-comment.png`.

| Loại | Chụp gì | Ghi chú |
|---|---|---|
| `comment` | Comment của bot cho PR | Chạy `uv run pr-triage publish --result <thu-muc>/triage-result.json --slug <owner/repo> --pr <so> --db data/team/store.sqlite` **không có** `--post`: lệnh chỉ in comment. Dán vào trình xem Markdown rồi chụp. Muốn đăng thật, xem đoạn dưới bảng |
| `terminal` | Lệnh `run` và dòng kết thúc có thời gian chạy | Một ảnh cho mỗi repo là đủ |
| `ket-qua` | Bảng `ket-qua.tsv` mở trong bảng tính | Một ảnh cho mỗi repo |
| `ca-dien-hinh` | Đoạn mã của ca điển hình (mục 7.3) | Chỉ với mã nguồn mở, hoặc repo cá nhân khi chủ repo đồng ý |

**Đăng comment thật lên PR (không bắt buộc).** Số đo và ảnh comment ở trên không cần đăng comment: chế độ mặc định của `run` chỉ ghi kết quả, và `publish` không có `--post` in đúng nội dung comment. Chỉ đăng thật khi cần ảnh bot comment trên giao diện GitHub cho slide demo. Mỗi người một hoặc hai PR là đủ.

- **Không bao giờ đăng lên PR của repo gốc mã nguồn mở.** Đó là spam lên dự án của người khác.
- `--post` đăng bằng token trong biến môi trường `GITHUB_TOKEN`, nên PR phải nằm trên repo bạn có quyền comment.
- **Repo cá nhân:** tạo PR như bình thường rồi chạy `publish --post`.
- **Repo mã nguồn mở:** fork về tài khoản mình rồi dựng lại PR trong bản fork. Đẩy hai SHA thành hai nhánh:

  ```bash
  git -C data/raw/<ma-repo> remote add fork https://github.com/<tai-khoan>/<repo>.git
  git -C data/raw/<ma-repo> push fork <sha-base>:refs/heads/base-pr<so> <sha-head>:refs/heads/pr<so>
  ```

  Mở PR từ `pr<so>` vào `base-pr<so>` **trong bản fork** (khi tạo PR, chọn repo đích là bản fork, không phải repo gốc). Sau đó:

  ```bash
  uv run pr-triage publish --result <thu-muc>/triage-result.json \
    --slug <tai-khoan>/<repo> --pr <so-pr-tren-fork> --db data/team/store.sqlite --post
  ```

- Comment trên bản fork công khai cũng là công khai. Chỉ đăng khi mã của repo đó đã công khai.

Khi chụp:

- Không để lộ khóa LLM, nội dung `.env`, token, đường dẫn có tên người dùng máy.
- Cắt sát vùng cần xem, dùng giao diện sáng, chữ đủ lớn để chiếu.
- Không chụp mã của công ty hay dữ liệu cá nhân trong repo.

### 7.3. Ca điển hình

Chọn 3–5 cảnh báo mỗi người, ghi vào `ca-dien-hinh.md`. Ưu tiên các loại sau, mỗi loại ít nhất một ca trong cả nhóm:

1. B và C cùng loại đúng một cảnh báo sai.
2. B loại nhầm, C giữ đúng một lỗi thật (hoặc ngược lại).
3. Ngữ cảnh luồng dữ liệu của C cho thấy hàm làm sạch nằm ở hàm khác.
4. LLM trả `unknown` hoặc nêu phần ngữ cảnh còn thiếu.
5. LLM sai rõ ràng, để minh họa giới hạn.

Mỗi ca ghi: mã luật và CWE, file và dòng, đoạn mã (tối đa khoảng 15 dòng), nhãn và giải thích của B, nhãn và giải thích của C, nhãn người gán, một câu nhận xét. Nhãn người gán chỉ điền sau khi đã gán mù (mục 6), không điền trước.

Giải thích của B và C nằm trong trường `explanation` của từng nhận định trong `triage-result.json`.

### 7.4. Số liệu và hình cho cả nhóm

Người tổng hợp làm sau khi gán nhãn xong:

- `uv run pr-triage eval metrics --split eval --markdown --db data/team/store.sqlite`: bảng số đo từng cách kèm khoảng tin cậy.
- `uv run pr-triage eval export --split eval --db data/team/store.sqlite`: số liệu tổng hợp ẩn danh vào `reports/results/summary.json`.
- Biểu đồ cho slide vẽ từ `reports/results/`, không vẽ từ số chép tay.
- Ảnh và ca điển hình đã làm sạch được đưa vào `docs/test-records/<ngày>/results/` theo quy ước hồ sơ kiểm thử. Ảnh thô giữ ở `data/`.

## 8. Quy tắc dữ liệu

- Không commit mã của repo đã chọn, kết quả quét thô, file SQLite hay phiếu gán nhãn. Tất cả nằm trong `data/`.
- Chỉ số liệu tổng hợp từ `pr-triage eval export` mới vào `reports/results/`.
- Không ghi khóa LLM vào file nào ngoài `.env`.
- Báo cáo gọi tập dữ liệu này là "repo mã nguồn mở và repo cá nhân", không gọi là "công ty Z".

## 9. Danh sách kiểm tra trước khi nộp

- [ ] Repo thỏa R1–R5, không thuộc danh sách loại trừ, đã đăng ký không trùng.
- [ ] Ít nhất 5 PR, mỗi PR có ít nhất 1 cảnh báo mới, tổng ít nhất 20 cảnh báo.
- [ ] Danh sách PR chốt trước khi chạy B và C.
- [ ] Chạy bằng tham số chung của nhóm, `rulesets.lock` khớp mã băm.
- [ ] Có `loc-a.tsv`, `ket-qua.tsv`, `thong-tin-repo.md`, `nhat-ky.md`.
- [ ] Có ảnh `comment`, `terminal`, `ket-qua` và 3–5 ca điển hình; ảnh không lộ khóa hay đường dẫn cá nhân.
- [ ] Không có gì từ `data/` trong `git status`.
