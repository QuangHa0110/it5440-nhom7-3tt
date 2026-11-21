# Đề xuất hướng làm đề tài 3TT (Sơn)

**Cổng bảo mật pull request có LLM lọc, triển khai tại công ty Z: đo giá trị thật ở tỷ lệ cảnh báo sai thật**

Tên tiếng Anh dự kiến: *Does LLM Triage Pay Off in Practice? A Case Study of a PR-Time Security Gate at a Vietnamese Software Company*

| | |
|---|---|
| Người đề xuất | Sơn, nhánh `son-dev` |
| Ngày | 07/11/2026 |
| Trạng thái | Đề xuất để nhóm chọn ý tưởng, **chưa chốt** |
| Căn cứ | [docs/khao-sat/tong-quan-tai-lieu.md](khao-sat/tong-quan-tai-lieu.md) (61 tài liệu 2023–2026), 4 bài báo được giao, hướng dẫn tiểu luận của thầy |
| Quan hệ với bản nháp | Dùng lại gần hết `docs/proposal-3TT.md` (nhánh `docs/proposal-3tt`), chỉ đổi trọng tâm. Xem mục 7 |

## 1. Tóm tắt

Gợi ý nội dung tóm tắt để dán vào nhóm chat:

1. Hướng so sánh A/B/C/D trên PR dựng từ CVE đã khá đông. Từng nhánh đều đã có công trình rất gần, công bố năm 2026 (mục 2). Nếu chỉ làm phần đó, nhóm khó có đóng góp mới, và cũng không đạt điều kiện điểm A vì thiếu công ty.
2. Khoảng trống còn lại nằm đúng ở phần **công ty Z** mà bản nháp đang tạm gác. Chưa thấy nghiên cứu nào đo *lập trình viên có sửa không* đối với cảnh báo bảo mật đã qua LLM lọc trên PR thật.
3. Đề xuất: triển khai một bot comment **không chặn merge** trong CI của Z. Bot gồm công cụ quét + LLM lọc. Các cách còn lại chạy ngầm trên cùng PR để so sánh. Nhóm đo năm thứ: cảnh báo sai giảm bao nhiêu, lỗi thật bị lọc mất bao nhiêu, lập trình viên sửa bao nhiêu, chi phí mỗi PR, và mô hình chạy cục bộ so với cloud.
4. Khối lượng vừa sức, vì dùng lại pipeline, định dạng dữ liệu và cách A–D của bản nháp. Bộ CVE thu nhỏ còn 30 cặp, chỉ để hiệu chuẩn.
5. Điều kiện sống còn là **chốt được công ty Z trước 11/11**. Nếu không có công ty, quay về bản nháp đã cắt gọn và nhắm điểm B (mục 6).

## 2. Khảo sát nói gì, và vì sao phải đổi trọng tâm

| Nhận định | Bằng chứng (chi tiết trong file khảo sát) |
|---|---|
| LLM lọc cảnh báo SAST đã có nhiều nghiên cứu | "Sifting the Noise" (ISSTA 2026) so sánh 3 agent lọc cảnh báo CodeQL trên dự án Java thật, nhận ra tới 93,3% cảnh báo sai [1]. Tencent (ICSE-SEIP 2026) loại được 94–98% cảnh báo sai trên 433 cảnh báo trong công nghiệp [2]. IRIS, ZeroFalse, LLM4FPM [3–5] |
| Dựng PR bằng cách đảo ngược commit vá đã có người làm | SEVRA-BENCH dựng khoảng 1.000 PR theo đúng cách này để đo agent review có bị lừa không [6]. SecPRBench (10/2026) dùng commit gây lỗi thật và phê phán benchmark dựng từ bản vá là thiếu thực tế [7] |
| Đưa cảnh báo SAST cho LLM (cách D) đã có kết quả | 96,9% phát hiện khi LLM được đối chiếu với SAST [8] |
| Dữ liệu CVE công khai bị nghi đã nằm trong dữ liệu huấn luyện của mô hình | QLCoder: tỉ lệ thành công 57,7% trên CVE trước 2025 nhưng chỉ 46,2% trên CVE 2025 [9]. PrimeVul: F1 giảm từ 68% xuống 3% trên dữ liệu sạch [10] |
| **Còn trống:** đo hiệu quả trên mã và người thật | Mức giảm 94–98% đều đo ở nơi có 76–92% cảnh báo sai [1], [2]. Bài vệ tinh chỉ có 22,2% cảnh báo sai (KTC 95%: 17,6–27,6%) [11]. Google và Facebook đo bằng hành động của lập trình viên [12], [13], nhưng chưa ai áp cách đo này cho cảnh báo bảo mật đã qua LLM lọc. Chưa thấy so sánh mô hình mở chạy cục bộ với cloud cho việc này, cũng chưa thấy nghiên cứu DevSecOps nào ở Việt Nam |

"Chưa thấy" nghĩa là nhóm chưa tìm được trong khảo sát, không phải đã chứng minh là không có. Khi viết báo cáo, dùng cụm "theo hiểu biết của chúng tôi".

**Ví dụ minh họa vì sao tỉ lệ cảnh báo sai nền quan trọng.** Giả sử bộ lọc loại được 95% cảnh báo sai nhưng cũng loại nhầm 5% lỗi thật.

- Trên 100 cảnh báo có 90 cảnh báo sai (kiểu OWASP Benchmark): bộ lọc bớt 85,5 lượt đọc và mất 0,5 lỗi thật. Tức khoảng 171 lượt đọc tiết kiệm cho mỗi lỗi thật bị mất.
- Trên 100 cảnh báo có 22 cảnh báo sai (như bài vệ tinh): bộ lọc chỉ bớt 20,9 lượt đọc mà mất 3,9 lỗi thật. Tức khoảng 5,4 lượt cho mỗi lỗi thật bị mất.

Cùng một bộ lọc, giá trị chênh khoảng 30 lần. Muốn biết bộ lọc có đáng dùng ở công ty Z không thì phải đo trên dữ liệu của Z.

## 3. Năm phương án đã cân nhắc

Thang điểm từ 1 đến 5 sao là đánh giá chủ quan, dựa trên khảo sát.

| | P1. Cổng PR có LLM lọc tại Z (**đề xuất**) | P2. Sự cố cũ → luật Semgrep | P3. Phễu lọc secret | P4. SCA + reachability + VEX | P5. Bản nháp A/B/C/D trên CVE |
|---|---|---|---|---|---|
| Ý tưởng | Công cụ quét + LLM lọc, comment trên PR của Z. Các cách khác chạy ngầm để so sánh | Từ các commit vá bảo mật cũ của Z, LLM sinh luật "báo trên bản lỗi, im trên bản vá" như QLCoder. Chạy lại lịch sử để xem luật có chặn được lỗi tái phát không | Gitleaks/TruffleHog tìm ứng viên, LLM lọc, đo độ chính xác trên repo của Z | Lọc cảnh báo thư viện theo việc mã lỗi có được gọi tới không, rồi LLM sinh VEX | So sánh 4 cách trên 40–60 PR dựng từ Vul4J/Project KB |
| Khả thi trong 3 tuần | ★★★★ | ★★★ | ★★★★★ | ★★ | ★★★★ |
| Mức mới | ★★★★ | ★★★★★ | ★★ | ★★★★ | ★★ |
| Đo được hiệu quả tại Z | ★★★★★ trực tiếp | ★★★ gián tiếp | ★★★★ | ★★★ | ☆ không đo được |
| Phụ thuộc Z | Cao | Rất cao: cần ≥ 20 commit vá bảo mật | Trung bình | Trung bình | Không |
| Khớp Chương 11 | 11.2–11.8, 11.10 | 11.2, 11.11, 11.12 | 11.10 (hơi hẹp) | 11.9 | 11.2–11.8 |
| Rủi ro chính | Z cấp quyền chậm, ít PR | Z không có đủ lịch sử vá; luật bám sát mẫu quá | Ít phát hiện, mỏng về phân tích chương trình | Gán nhãn tốn vài giờ mỗi ca; công cụ reachability miễn phí chỉ tốt cho Go | Bị xem là làm lại nghiên cứu đã có; không đạt điểm A |
| Điểm kỳ vọng | A nếu có Z | A nếu Z có dữ liệu | B+ | B+ | B |

**Chọn P1 làm lõi**, vì đây là phương án duy nhất vừa khả thi, vừa có điểm mới, vừa thấy được hiệu quả tại công ty. Phần còn lại dùng như sau:

- **P5:** thu nhỏ, giữ làm bước hiệu chuẩn công cụ (RQ4).
- **P2:** phần mở rộng có điều kiện, chỉ làm nếu tuần đầu kiểm tra thấy Z có đủ commit vá.
- **P3:** bật sẵn trong pipeline cho rẻ. Đây cũng là phương án dự phòng khi PR sinh quá ít cảnh báo SAST.

## 4. Đề xuất chính (P1)

### 4.1. Luồng triển khai

```text
Lập trình viên mở PR ở công ty Z
  → CI (Jenkins/GitLab CI/GitHub Actions, theo hệ thống Z đang dùng) chạy công cụ quét:
      Semgrep, SpotBugs+FindSecBugs nếu là Java, Gitleaks, OSV-Scanner
  → Script chuẩn hóa, khử trùng lặp bằng dấu vân tay, chỉ giữ cảnh báo mới so với nhánh chính
  → Script xếp ưu tiên: cộng điểm khi gọi tới API nguy hiểm (sink, theo GONDAR)
      và khi dữ liệu đi từ ngoài vào
  → LLM lọc từng cảnh báo: likely_real / likely_false / unknown, kèm lý do   ← cách B
  → Bot đăng MỘT comment tổng hợp, không chặn merge
  → Lập trình viên xử lý: sửa / phản hồi / bấm "không đúng" / bỏ qua         ← dữ liệu RQ3

Chạy ngầm trên cùng PR, không đăng lên PR: A (chỉ công cụ), B với mô hình thứ hai,
và D (agent đọc PR kèm cảnh báo) nếu đủ ngân sách                            ← dữ liệu RQ1, RQ2
```

Định dạng `finding`, `report`, `run.json` và các lệnh `python -m core.*` dùng nguyên theo `docs/quy-uoc-chung.md` của bản nháp.

### 4.2. Liên hệ với 4 bài báo được giao

| Bài | Nhóm dùng gì |
|---|---|
| Vệ tinh [11] | Kiến trúc pipeline nhiều lớp (SAST, SCA, secret), khử trùng lặp bằng dấu vân tay, cách ước lượng tỉ lệ cảnh báo sai bằng mẫu ngẫu nhiên kèm khoảng tin cậy 95%, phân tích độ nhạy theo từng công cụ |
| QLCoder [9] | Tiêu chí "báo trên bản lỗi, im lặng trên bản đã vá" cho bộ hiệu chuẩn (RQ4) và cho luật sinh ra ở phần mở rộng (RQ5) |
| GONDAR [14] | Ý tưởng tập trung vào sink: cảnh báo có lời gọi tới sink nguy hiểm (`Runtime.exec`, truy vấn SQL, thao tác file, giải tuần tự hóa) được ưu tiên. LLM xét sink có thật sự với tới và khai thác được không |
| P2Patch [15] | Nguyên tắc tách oracle: bằng chứng dùng để chỉnh prompt hay luật không được dùng lại để chấm. Thể hiện qua việc chia `dev`/`eval` và việc người chấm không biết cảnh báo đến từ cách nào. Phần mở rộng: kiểm tra bản vá bằng test PoV |

### 4.3. Câu hỏi nghiên cứu

| RQ | Câu hỏi | Giả thuyết có thể bác bỏ | Dữ liệu |
|---|---|---|---|
| **RQ1** Hiện trạng và lọc | Trên mã của Z, công cụ quét báo bao nhiêu cảnh báo sai? LLM lọc bớt được bao nhiêu cảnh báo sai, và lọc nhầm bao nhiêu lỗi thật? | Ở tỉ lệ cảnh báo sai của Z, số lượt đọc tiết kiệm trên mỗi lỗi thật bị mất thấp hơn ít nhất 10 lần so với cùng bộ lọc chạy trên OWASP Benchmark | 200–400 cảnh báo đã gán nhãn, lấy từ việc chạy lại trên PR đã merge, PR mới và nhánh chính |
| **RQ2** Mô hình và ngữ cảnh | Mô hình mở chạy cục bộ khác mô hình cloud thế nào về độ chính xác, số lỗi thật bị lọc mất, chi phí và thời gian? Thêm ngữ cảnh riêng của Z (framework, hàm làm sạch dữ liệu nội bộ) có thu hẹp khoảng cách không? | Có ngữ cảnh của Z thì khoảng cách F1 giữa mô hình cục bộ và cloud giảm xuống dưới một ngưỡng chốt trước | Cùng bộ nhãn của RQ1, chạy offline trong máy của Z |
| **RQ3** Lập trình viên | Cảnh báo hiện lúc mở PR có được sửa nhiều hơn danh sách cảnh báo gửi theo lô không? Tỉ lệ cảnh báo sai mà lập trình viên cảm nhận được, và thời gian CI tăng thêm, là bao nhiêu? | Tỉ lệ được sửa lúc PR cao hơn tỉ lệ của báo cáo theo lô | Log bot, phản hồi trên comment, commit sau comment, khảo sát ngắn |
| **RQ4** Hiệu chuẩn | Trên 30 cặp CVE (bản lỗi và bản vá) đã bỏ thông tin lộ đáp án, thứ tự xếp hạng các cách có giống trên mã của Z không? Kết quả chênh bao nhiêu giữa CVE cũ và CVE năm 2026? | Trên CVE cũ, mô hình đạt kết quả tốt hơn rõ rệt so với CVE năm 2026 (dấu hiệu mô hình đã thuộc lòng CVE) | Vul4J/Project KB cùng các CVE năm 2026, kèm câu hỏi thử "đây là CVE nào?" |
| RQ5 (mở rộng) | Luật Semgrep do LLM sinh từ sự cố trước thời điểm t có bắt được sự cố sau t không? | Tỉ lệ sinh luật đúng trên mã Z không vượt 46,2%, mức của QLCoder trên CVE 2025 [9] | 20–60 commit vá bảo mật của Z |

**RQ1 cũng là phần "khảo sát hiện trạng"** mà thầy yêu cầu. Phần này gồm hai việc:

- Phỏng vấn trưởng nhóm kỹ thuật của Z trong 30 phút: hiện đang dùng công cụ gì, quy trình review ra sao, đã từng gặp sự cố bảo mật nào.
- Quét nền trên nhánh chính.

### 4.4. Đóng góp và triết lý

**Đóng góp dự kiến:**

- **C1.** Theo hiểu biết của nhóm, đây là số liệu công nghiệp đầu tiên về việc lập trình viên hành động thế nào với cảnh báo bảo mật đã qua LLM lọc, hiện ngay lúc mở PR. Số liệu đo tại một doanh nghiệp phần mềm Việt Nam.
- **C2.** Phân tích theo tỉ lệ cảnh báo sai nền: lọc mất bao nhiêu lỗi thật, và tiết kiệm bao nhiêu giờ công.
- **C3.** So sánh mô hình mở chạy cục bộ với mô hình cloud, kèm thử nghiệm tăng dần ngữ cảnh riêng của doanh nghiệp, trên mã chắc chắn chưa có trong dữ liệu huấn luyện của mô hình.
- **C4.** Quy trình và mã nguồn để doanh nghiệp khác lắp vào CI, cùng giao thức hiệu chuẩn có kiểm soát việc mô hình thuộc lòng CVE.

**Triết lý khoa học:**

- *Cảnh báo chỉ có giá trị khi lập trình viên hành động theo nó.* Google định nghĩa "effective false positive" là cảnh báo mà lập trình viên không làm gì [12]. Facebook ghi nhận cùng một bộ phân tích được sửa gần 0% khi gửi theo lô, nhưng trên 70% khi hiện lúc review [13].
- LLM chỉ đề xuất. Mức độ nghiêm trọng do script tính, và con người quyết định.
- Bằng chứng dùng để tạo kết quả không được dùng để chấm chính kết quả đó [15].
- Mọi giả thuyết phải bác bỏ được. Kết quả âm, ví dụ LLM lọc không đáng dùng ở Z, vẫn được báo cáo trung thực.
- Đây là **nghiên cứu trường hợp** (case study) theo chuẩn ACM SIGSOFT [16]. Mục đích là hiểu sâu một trường hợp, không khái quát cho mọi công ty. Giao thức và giả thuyết được commit lên repo trước khi chạy để có dấu thời gian.

### 4.5. Đo lường

| Nhóm | Chỉ số | Cách tính | Mốc so sánh |
|---|---|---|---|
| Lọc | Tỉ lệ loại cảnh báo sai | Số cảnh báo sai bị lọc / tổng số cảnh báo sai | Tencent 94–98% [2] |
| | Tỉ lệ lọc mất lỗi thật | Số lỗi thật bị lọc / tổng số lỗi thật. **Lấy mẫu dư** trong nhóm cảnh báo bị lọc | Semgrep chấp nhận lọc kém đi để giữ lỗi thật [17] |
| | Giá trị ròng | Lượt đọc tiết kiệm / lỗi thật bị mất; giờ công tiết kiệm = số cảnh báo sai bị lọc × thời gian xử lý một cảnh báo | Thủ công mất 10–20 phút mỗi cảnh báo [2] |
| Hành động | Tỉ lệ được sửa lúc PR | Số cảnh báo đã đăng mà dòng bị báo được sửa trước khi merge / số cảnh báo đã đăng | Facebook trên 70% [13], Atlassian 38,7% [18] (review chung, không riêng bảo mật) |
| | Tỉ lệ được sửa theo lô | Như trên, với danh sách cảnh báo trên nhánh chính gửi cho lập trình viên | Facebook gần 0% [13] |
| | Tỉ lệ cảnh báo sai hiệu dụng | Số cảnh báo lập trình viên đánh "không đúng" hoặc bỏ qua / số cảnh báo đã đăng | Google đặt ngưỡng dưới 10% [12] |
| Chi phí | Thời gian CI thêm vào | Trung vị và p90 trên mỗi PR | Bản nháp đặt mục tiêu dưới 15 phút |
| | Tiền | USD trên mỗi cảnh báo và mỗi PR, kể cả chi phí máy khi chạy mô hình cục bộ | Tencent 0,0011–0,12 USD/cảnh báo [2] |
| Cảm nhận | Khảo sát | 5–8 câu Likert về tính hữu ích và độ dễ dùng, kèm 3–5 phỏng vấn ngắn | |

**Thống kê.** Tỉ lệ kèm khoảng tin cậy 95% Wilson. So sánh hai cách trên cùng bộ cảnh báo bằng McNemar. Độ đồng thuận giữa người chấm đo bằng Cohen's kappa, dưới 0,6 thì sửa tiêu chí và chấm lại. Con số nào cũng ghi kèm mẫu số. Với 300 cảnh báo, khoảng tin cậy quanh 50% rộng khoảng ±5,7 điểm.

**Đáp án trên PR thật.** PR thật không có đáp án đầy đủ, nên một lỗi được coi là thật khi:

- ít nhất một cách trong A–D báo lỗi đó, và
- hai người chấm xác nhận, có một lập trình viên của Z chấm trên một tập con.

Báo cáo nêu rõ đây là ước lượng dựa trên hợp nhất các nguồn, vì lỗi mà không cách nào báo thì không đo được.

### 4.6. Phạm vi

| Hạng mục | Tối thiểu, đủ cho điểm A | Mở rộng, nếu kịp |
|---|---|---|
| Triển khai | 1–3 repo của Z, bot cách B comment không chặn trong ≥ 2 tuần, chạy lại trên 100–200 PR đã merge, 1 báo cáo theo lô | Thêm repo, comment inline cho Critical/High |
| Cách so sánh | A, B-cloud, B-cục bộ | Thêm D, rồi C |
| Ngữ cảnh | 2 mức: prompt chung, prompt có ghi chú về Z | 4 mức, có nhớ lịch sử phân loại |
| Gán nhãn | ≥ 200 cảnh báo, có kappa | ≥ 400 cảnh báo, 2 lập trình viên Z |
| Hiệu chuẩn | 30 cặp CVE đã bỏ thông tin lộ đáp án | 50 cặp, thêm CVE 2026 |
| Secret, thư viện | Chạy và báo riêng, không tính vào RQ1–RQ3 | Thêm LLM lọc secret, đo độ chính xác |
| RQ5 | Không làm | Chỉ làm nếu cuối tuần 1 thấy Z có ≥ 20 commit vá bảo mật |
| Xác nhận | Thư xác nhận của công ty (phụ lục A) | Z duyệt bản thảo trước khi đăng arXiv |

Không làm: viết công cụ quét mới, train mô hình, fuzzing, viết exploit cho hệ thống của Z, tự động sửa mã.

**Khối lượng gán nhãn:** 300 cảnh báo × khoảng 15 phút = khoảng 75 giờ công, tức khoảng 11 giờ mỗi người.

### 4.7. Công cụ và môi trường

| Stack của Z | SAST | Thư viện | Secret |
|---|---|---|---|
| Java | Semgrep, SpotBugs + FindSecBugs | OSV-Scanner, OWASP Dependency-Check | Gitleaks |
| JS/TS | Semgrep | OSV-Scanner, `npm audit` | Gitleaks |
| Python | Semgrep, Bandit | OSV-Scanner | Gitleaks |
| Go | Semgrep, gosec | govulncheck (có phân tích lời gọi) | Gitleaks |

- **Mô hình cloud:** chỉ dùng khi Z đồng ý bằng văn bản.
- **Mô hình mở cục bộ:** một mô hình code cỡ 7–32B chạy qua Ollama hoặc vLLM trên máy của Z. Tên mô hình chốt sau khi biết cấu hình máy.
- **Dữ liệu:** toàn bộ dữ liệu thô nằm trong Z. Chỉ xuất CSV tổng hợp đã ẩn danh, đúng quy tắc của repo. Giá trị secret được che trước khi gửi cho LLM.
- **Tách oracle:** chia `dev`/`eval` theo repo hoặc theo thời gian. Chỉ chỉnh prompt trên `dev`, gắn tag Git trước khi chạy `eval`.

## 5. Kế hoạch theo mốc của thầy

| Thời gian | Việc | Kết quả |
|---|---|---|
| **Đến 11/11** | Chốt ý tưởng và công ty Z, ký thỏa thuận dùng dữ liệu, chốt có được dùng cloud không. Kiểm kê: số PR mỗi tuần, stack, CI, số commit vá bảo mật. Phỏng vấn hiện trạng. Dựng pipeline trên 1 repo | Quyết định có làm RQ5 không, và dùng cloud hay chỉ cục bộ |
| 12–17/11 | Chạy lại trên PR đã merge và quét nhánh chính. Chạy cách A, gán nhãn đợt 1. Bật bot ở chế độ chạy ngầm. Chạy 30 cặp hiệu chuẩn | Số liệu hiện trạng (RQ1 phần A) |
| **18–19/11 Báo cáo lần 1** | Nội dung 1 (khảo sát) và nội dung 2 (RQ, hiện trạng, quy trình) | |
| 18–24/11 | Bật comment trên PR thật, gửi báo cáo theo lô. Chạy offline các tổ hợp mô hình × ngữ cảnh. Gán nhãn đợt 2, tính kappa | RQ1, RQ2, RQ4 |
| **25–26/11 Báo cáo lần 2** | Thêm nội dung 3 (đóng góp, triết lý, phương pháp đo) cùng số liệu sơ bộ | |
| 27/11–12/2026 | Thu số liệu hành động, khảo sát, phỏng vấn. Lập trình viên Z xác nhận lại kết quả, xin thư xác nhận. Viết bản arXiv, báo cáo đầy đủ, slide | RQ3 và sản phẩm nộp |

**Gợi ý chia việc** để khớp 7 phần của bản nháp:

| Số người | Phụ trách |
|---|---|
| 1 | Đầu mối với Z, kiêm phụ trách đạo đức dữ liệu |
| 2 | Pipeline và bot |
| 2 | LLM và các tổ hợp mô hình × ngữ cảnh |
| 1 | Hiệu chuẩn và RQ5 |
| 1 | Phân tích số liệu và viết báo cáo |

Cả nhóm cùng gán nhãn, trừ người trực tiếp viết prompt.

## 6. Nếu không có công ty Z

- **Vẫn không có Z trước 11/11:** quay về P5. Cắt gọn còn 30–50 cặp, áp dụng các biện pháp chống nhiễm bẩn ở mục 7, và báo cáo theo từng lớp. Nhắm điểm B và nói rõ với thầy.
- **Phương án trung gian:** chạy P1 trên công ty nơi một thành viên đang làm, hoặc trên một công cụ nội bộ nhỏ ít nhạy cảm của Z. Đây là mức 1 và mức 3 trong bảng các mức hợp tác của bản nháp.
- **Không coi là thay thế được công ty:** lấy repo mã nguồn mở rồi gọi đó là "công ty Z". Cách này không đo được hành động thật, và hướng dẫn chấm của thầy yêu cầu xác nhận của công ty.

## 7. Góp ý cho bản nháp `docs/proposal-3TT.md`

Bản nháp đã kỹ, nhất là các phần quy tắc an toàn, định dạng dữ liệu và quy tắc chấm. Nên **giữ gần như toàn bộ**, chỉ sửa 6 điểm sau:

| # | Sửa | Lý do |
|---|---|---|
| 1 | Đưa công ty Z lên làm phần chính. A/B/C/D trở thành dụng cụ đo chạy ngầm, không còn là đối tượng nghiên cứu chính | Câu hỏi "cách nào tốt nhất trên CVE công khai" đã có nhiều bài trả lời [1], [6], [7], [8]. Điểm A cần hiệu quả tại công ty |
| 2 | Bộ CVE giảm từ 40–60 + 40–60 xuống 30 cặp. Viết lại mô tả PR cho trung tính, thêm CVE 2026, hỏi thử "đây là CVE nào?" | Đỡ tốn công dựng dữ liệu (rủi ro lớn nhất trong bản nháp), và kiểm soát được việc mô hình thuộc lòng CVE [9], [10]. Vul4J chỉ có 79 lỗ hổng và một số không còn build được |
| 3 | Báo cáo chỉ số riêng cho lỗi thật và cảnh báo sai, có tỉ lệ lọc mất lỗi thật, thay vì chỉ một con số "độ chính xác" chung | Con số gộp thường đẹp hơn thực tế [17] |
| 4 | Không cho agent quyền ghi vào test PoV, và không cho agent thấy test PoV | Có bằng chứng agent sửa test để qua oracle (xem file khảo sát) |
| 5 | Ghi chi phí và thời gian cho từng PR ngay từ đầu | Đóng góp rẻ nhất, chưa thấy ai công bố từ CI thật |
| 6 | Không mặc định Jenkins và Java. Chọn theo stack của Z | Tăng khả năng tìm được công ty phù hợp |

## 8. Cần quyết định

**Nhóm, trước 09/11:**

1. Chọn P1 hay giữ P5?
2. Ai có thể giới thiệu công ty Z? Cần một nhóm dự án dùng Git, có PR/MR và CI, khoảng ≥ 10 PR mỗi tuần.
3. Ngân sách cho LLM cloud, và có máy GPU để chạy mô hình cục bộ không?

**Hỏi thầy:**

1. Công ty nơi một thành viên đang làm có được tính là công ty Z không?
2. Thư xác nhận cần theo hình thức nào?
3. Nghiên cứu trường hợp với 1–3 repo trong khoảng 2 tuần có đủ "thấy hiệu quả" không?

**Hỏi công ty Z:**

1. Có được gửi mã ra LLM cloud không?
2. Được thêm stage chỉ comment trong ít nhất 2 tuần không?
3. Có 1–2 lập trình viên trả lời khảo sát và chấm thử khoảng 50 cảnh báo không?
4. Có đồng ý công bố số liệu tổng hợp đã ẩn danh không?

## Phụ lục A. Nội dung thư xác nhận của công ty (dự kiến)

1. Thời gian và phạm vi triển khai: số repo, số PR, chế độ chỉ comment.
2. Bảng số liệu tổng hợp mà nhóm công bố, do công ty đối chiếu với log nội bộ.
3. Công ty đồng ý công bố dưới tên ẩn danh "công ty Z", kèm mô tả chung về ngành và quy mô.
4. Nhận xét ngắn của trưởng nhóm kỹ thuật về việc có tiếp tục dùng quy trình hay không.
5. Chữ ký và ngày.

## Tài liệu tham khảo

Danh sách đầy đủ 61 tài liệu, kèm đánh dấu các nguồn chưa xác minh, nằm trong [khao-sat/tong-quan-tai-lieu.md](khao-sat/tong-quan-tai-lieu.md).

[1] Y. Xiong and T. Zhang, "Sifting the noise: A comparative study of LLM agents in vulnerability false positive filtering," in *Proc. ISSTA*, 2026, arXiv:2601.22952.

[2] X. Du và cộng sự, "Reducing false positives in static bug detection with LLMs: An empirical study in industry," in *Proc. ICSE-SEIP*, 2026, arXiv:2601.18844.

[3] Z. Li, S. Dutta, and M. Naik, "IRIS: LLM-assisted static analysis for detecting security vulnerabilities," in *Proc. ICLR*, 2025, arXiv:2405.17238.

[4] M. Iranmanesh và cộng sự, "ZeroFalse: Improving precision in static analysis with LLMs," arXiv:2510.02534, 2025.

[5] Chen và cộng sự, "Utilizing precise and complete code context to guide LLM in automatic false positive mitigation," arXiv:2411.03079.

[6] R. Melo và cộng sự, "SEVRA-BENCH: Social engineering of vulnerabilities in review agents," arXiv:2606.13757, Jun. 2026.

[7] Y. Yang và cộng sự, "Can agentic code review catch vulnerabilities before they are merged?," arXiv:2610.33509, Oct. 2026.

[8] S. Thornton, "Can adversarial code comments fool AI security reviewers…," arXiv:2602.16741, Feb. 2026.

[9] C. Wang, Z. Li, S. Dutta, and M. Naik, "QLCoder: A query synthesizer for static analysis of security vulnerabilities," arXiv:2511.08462, 2026.

[10] Y. Ding và cộng sự, "Vulnerability detection with code language models: How far are we?," in *Proc. ICSE*, 2025, arXiv:2403.18624.

[11] R. Idan, T. Cohen Galor, A. Shabtai, and Y. Elovici, "An empirical security analysis of open-source software used in onboard satellite systems," arXiv:2609.15425, Sep. 2026.

[12] C. Sadowski, E. Aftandilian, A. Eagle, L. Miller-Cushon, and C. Jaspan, "Lessons from building static analysis tools at Google," *Commun. ACM*, vol. 61, no. 4, pp. 58–66, 2018.

[13] D. Distefano, M. Fähndrich, F. Logozzo, and P. W. O'Hearn, "Scaling static analyses at Facebook," *Commun. ACM*, vol. 62, no. 8, pp. 62–70, 2019.

[14] F. Fleischer và cộng sự, "Contextualizing sink knowledge for Java vulnerability discovery," arXiv:2604.01645, 2026.

[15] M. Iranmanesh và cộng sự, "P2Patch: Exploit-guided vulnerability repair," arXiv:2610.20245, Oct. 2026.

[16] ACM SIGSOFT, "Empirical standards: Case study." [Online]. Available: https://github.com/acmsigsoft/EmpiricalStandards

[17] Semgrep, "Building an AppSec AI that security researchers agree with 96% of the time," Semgrep Blog, 2025. (Số liệu do vendor tự báo cáo.)

[18] "RovoDev code reviewer: A large-scale online evaluation of LLM-based code review automation at Atlassian," in *Proc. ICSE-SEIP*, 2026, arXiv:2601.01129.
