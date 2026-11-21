# Proposal đề tài 3TT

**Tìm lỗi bảo mật thật trong pull request Java: so sánh công cụ phân tích tĩnh, LLM và agent, và đánh giá triển khai thực tế**

Tên tiếng Anh dự kiến: *Finding Real Security Bugs in Java Pull Requests: Comparing Static Analysis, LLMs and Agents in Practice*

| | |
|---|---|
| Học phần | IT5440 Nguyên lý và kỹ thuật phân tích chương trình, học kỳ 2026.1 |
| Nhóm | Nhóm 7, 7 học viên |
| Đề tài | 3TT, Chương 11: Phân tích chương trình hướng bảo mật, hướng đánh giá triển khai thực tế |
| Trạng thái | Bản nháp để cả nhóm góp ý, cập nhật ngày 07/11/2026 |

## 1. Tóm tắt đề xuất

Người review cần biết một điều: pull request này có lỗi bảo mật thật nào không. Đề tài xây dựng quy trình trả lời câu hỏi đó ngay trong Jenkins, rồi đăng kết quả thành một comment xếp từ Critical đến Low.

Nhóm so sánh bốn cách trên cùng một bộ pull request có đáp án: chỉ dùng công cụ quét, công cụ cộng LLM lọc, agent đọc trực tiếp pull request, và kết hợp công cụ với agent.

Nhóm không viết công cụ quét và không train LLM. Việc của nhóm là xây quy trình, tạo bộ dữ liệu đánh giá và đo kết quả.

**Đóng góp chính:** số liệu kiểm chứng được về việc cách nào tìm được nhiều lỗi thật nhất trên pull request Java, với ít báo sai nhất và chi phí chấp nhận được.

**Phạm vi hiện tại:** phần đo tại công ty Z đang tạm gác lại, không phải loại bỏ. Nhóm làm RQ1–RQ3 trên dữ liệu công khai và demo luồng pull request trên bản fork của một dự án Java mã nguồn mở.

## 2. Vấn đề

Công cụ quét có hai giới hạn. Chúng báo nhiều cảnh báo trùng và cảnh báo sai: bài báo về phần mềm vệ tinh ghi nhận 22.2% cảnh báo sai ngay cả sau khi làm sạch dữ liệu [1]. Chúng cũng chỉ thấy các lỗi đã có luật, nên có thể bỏ sót lỗi logic như thiếu kiểm tra quyền.

Chỉ phân loại cảnh báo thật hay sai thì chưa đủ, vì bước đó không tìm thêm được lỗi mà công cụ chưa báo. Lập trình viên cần một câu trả lời ở mức pull request: có lỗi thật nào cần sửa, hay không thấy lỗi mới.

## 3. Mục tiêu và tiêu chí thành công

Mục tiêu là tìm ra và triển khai cách phù hợp nhất để phát hiện lỗi bảo mật thật trên pull request của dự án Java dùng Git và Jenkins.

Ngưỡng đề xuất, cần cả nhóm chốt trước khi chạy thực nghiệm:

- Cách được chọn tìm được không ít lỗi thật hơn cách chỉ dùng công cụ.
- Trung bình không quá 3 báo cáo sai trên mỗi pull request.
- Thời gian thêm vào mỗi pull request không quá 15 phút.
- Mọi kết luận được chấm bằng bằng chứng độc lập với công cụ và LLM.

Các ngưỡng này là con số khởi điểm, chưa có căn cứ thực nghiệm.

## 4. Phạm vi

| Mức | Nội dung |
|---|---|
| **Phải có** | Chương trình lõi, quy trình quét, chuẩn hóa, khử trùng lặp, xếp ưu tiên, bốn cách A–D (mục 8.2), bộ pull request có đáp án, khung đánh giá, comment tổng hợp, demo trên bản fork |
| **Nên có** | Comment inline, một phiên bản LLM local của cách B |
| **Tạm gác** | Triển khai tại công ty Z và RQ4 |
| **Bỏ nếu thiếu thời gian** | Luật Semgrep tùy biến, quét cấu hình hạ tầng, thử thêm mô hình khác |
| **Không làm** | Viết công cụ quét mới, train LLM, săn lỗ hổng chưa biết, fuzzing, viết exploit, tự động sửa lỗi |

Số liệu đánh giá trên pull request chỉ chấm lỗi trong mã tự viết. Quét thư viện và secret vẫn chạy trong quy trình, nhưng được báo cáo riêng.

## 5. Cơ sở và khoảng trống nghiên cứu

| Nguồn | Đã làm được | Nhóm sử dụng |
|---|---|---|
| Phần mềm vệ tinh [1] | Quét 126 repo, gán nhãn 360 mẫu, 22.2% cảnh báo sai | Quy trình nhiều lớp, dấu vân tay, cách ước lượng tỉ lệ báo sai |
| QLCoder [2] | Agent LLM viết truy vấn CodeQL, F1 đạt 0.7 | Tiêu chí báo trên bản lỗi, im lặng trên bản đã vá |
| GONDAR [3] | LLM lọc sink kết hợp fuzzing, gấp 4 lần Jazzer | Ưu tiên vị trí gọi API nguy hiểm |
| P2Patch [4] | Vòng đối kháng tạo và kiểm tra bản vá, chấm bằng bộ đáp án riêng | Không dùng lại bằng chứng đã sinh ra kết quả để chấm chính kết quả đó |
| Vul4J [5], Project KB [6] | Bộ dữ liệu lỗ hổng Java kèm commit sửa lỗi | Nguồn tạo bộ pull request có đáp án |

**Khoảng trống dự kiến:** kết hợp công cụ quét với LLM đã có trong thực tế. Sourcegraph Sherlock [7] đưa cảnh báo của công cụ cho LLM đối chiếu nhưng theo nguồn tìm được không công bố số đo chính thức, còn Datadog [8] có sản phẩm lọc cảnh báo bằng LLM. Vì vậy, nhóm không nhận đây là ý tưởng mới. Điểm nhóm có thể đóng góp là một so sánh độc lập, tái lập được, trên pull request Java có đáp án.

Đây mới là giả thuyết. Tìm kiếm sơ bộ chỉ cho thấy các bài của doanh nghiệp, nên nhóm phải khảo sát kỹ arXiv, ACM và IEEE trong tuần đầu, rồi điều chỉnh đóng góp nếu đã có nghiên cứu trùng.

## 6. Câu hỏi nghiên cứu

| RQ | Câu hỏi | Dữ liệu |
|---|---|---|
| **RQ1** | Chỉ dùng công cụ quét thì tìm được bao nhiêu lỗi thật trên pull request, và báo sai bao nhiêu? | Bộ pull request |
| **RQ2** | Lọc bằng script và LLM giảm được bao nhiêu báo cáo sai, và làm mất bao nhiêu lỗi thật? | Bộ pull request |
| **RQ3** | Agent đọc trực tiếp pull request có tìm được lỗi mà công cụ bỏ sót không, và kết hợp hai nguồn có tốt hơn không so với chi phí? | Bộ pull request |
| **RQ4** (tạm gác) | Trên pull request thật, lập trình viên có hành động theo báo cáo không, và chi phí là gì? | Công ty Z |

## 7. Giải pháp

### 7.1. Luồng trên pull request

Luồng dưới đây là cách D, bản đầy đủ nhất. Bản triển khai cuối cùng sẽ theo cách thắng trong thực nghiệm.

```text
Lập trình viên mở pull request
  → Jenkins chạy công cụ quét
  → Script chuẩn hóa, khử trùng lặp và giữ cảnh báo mới so với nhánh chính
  → Agent đọc thay đổi, cảnh báo và repo, rồi xác nhận hoặc báo thêm lỗi
  → Script gộp kết quả và xếp từ Critical đến Low
  → Jenkins đăng comment lên pull request
  → Người review quyết định
```

Ngoài ra, Jenkins quét toàn bộ repo định kỳ, vì thư viện có thể bị công bố lỗ hổng mới dù mã không đổi.

**Cách kích hoạt.** Không xây web riêng, vì lập trình viên không nên phải làm thêm bước nào.

- Tự động: nền tảng Git gửi webhook khi có pull request.
- Kiểm tra định kỳ: dùng khi webhook không gọi được vào Jenkins.
- Chạy tay: dùng trang "Build with Parameters" của Jenkins để chọn repo, số pull request và cách A, B, C hoặc D.

**Chương trình lõi.** Toàn bộ xử lý nằm trong một chương trình Python. Jenkins, chạy tay và script chạy hàng loạt đều gọi chương trình này, nên thứ được đo trong thực nghiệm chính là thứ được triển khai:

```bash
python -m core.review --base main --head pr-branch --method D --out ket-qua.json
```

### 7.2. Các thành phần

| # | Thành phần | Thực hiện bằng | Nội dung |
|---|---|---|---|
| 1 | Pipeline quét | Jenkinsfile, công cụ có sẵn | SpotBugs + FindSecBugs, Semgrep, OWASP Dependency-Check, OSV-Scanner, Syft, Gitleaks |
| 2 | Chuẩn hóa | Python | Đưa kết quả về một bảng: nguồn, luật, CWE, file, dòng, mức độ |
| 3 | Khử trùng lặp | Python | Bỏ phần ngoài phạm vi, gộp cảnh báo trùng và giữ cảnh báo mới so với nhánh chính. Dấu vân tay gồm file, tên hàm, luật hoặc CWE và mã băm của đoạn mã đã chuẩn hóa, không dùng số dòng |
| 4 | Xếp ưu tiên | Python | Tính điểm theo mức nghiêm trọng, số nguồn cùng báo, API nguy hiểm và khả năng dữ liệu từ ngoài vào |
| 5 | LLM và agent | Python, LLM có sẵn | Lọc cảnh báo, đọc pull request, trả về JSON gồm CWE, vị trí, lý do và mức tin cậy. Script kiểm tra kết quả trước khi nhận |
| 6 | Bộ pull request và khung đánh giá | Python | Tạo pull request có đáp án, chạy bốn cách, chấm điểm, xuất bảng |
| 7 | Comment pull request | Script, API của nền tảng Git | Đăng và cập nhật một comment tổng hợp; thêm inline nếu kịp |

### 7.3. Phân chia trách nhiệm

| Bên | Làm | Không làm |
|---|---|---|
| Công cụ quét | Tìm cảnh báo theo luật | Kết luận cuối cùng |
| Script | Tổng hợp, lọc, tính mức độ, kiểm tra kết quả, đăng comment | Đọc hiểu ý nghĩa của mã |
| LLM và agent | Xác nhận cảnh báo, báo thêm lỗi, giải thích | Đổi mức độ, xóa cảnh báo, sửa mã, đăng comment |
| Con người | Quyết định sửa hay bỏ qua | |

Mức độ do script tính. Với lỗi chỉ agent báo, script suy ra mức độ từ CWE theo một bảng cố định, để kết quả không dao động giữa các lần chạy. Cảnh báo bị đánh giá là sai vẫn được giữ lại và xem được trong Jenkins.

### 7.4. Ví dụ comment

```markdown
## Kết quả quét bảo mật: 2 vấn đề mới

### Critical
**SQL Injection** (CWE-89), `UserController.java:42`
`id` lấy từ request và ghép thẳng vào câu SQL.
Gợi ý: dùng PreparedStatement.
Nguồn: FindSecBugs, Semgrep, agent.

### Low
...

Có 12 cảnh báo khác có thể là báo sai (xem trong Jenkins).
```

Nếu không có vấn đề nào, comment ghi rõ phạm vi đã kiểm tra, không khẳng định pull request an toàn.

Quy tắc đăng comment:

- Luôn có một comment tổng hợp duy nhất, được sửa lại khi có commit mới.
- Inline chỉ dùng cho Critical và High, tối đa khoảng 5 comment, và chỉ trên dòng thuộc thay đổi của pull request.
- Medium và Low chỉ nằm trong comment tổng hợp.
- Không báo lặp lại lỗi đã báo.

### 7.5. Quy tắc an toàn

- Chế độ ban đầu chỉ comment, không chặn merge.
- Comment không in giá trị secret, chỉ ghi file và loại secret.
- Coi mã trong pull request là không đáng tin, vì có thể chứa chú thích nhằm lừa LLM.
- Agent chạy trong môi trường cách ly, chỉ có quyền đọc và không giữ token. Agent chỉ trả về JSON.
- Chỉ Jenkins giữ token đăng comment, với quyền hẹp nhất có thể.
- Chủ dự án kiểm soát những ai được kích hoạt quét.
- Mã công ty chỉ gửi lên LLM cloud khi công ty cho phép.

### 7.6. Các xử lý kỹ thuật

| Tình huống | Cách xử lý |
|---|---|
| Thêm dòng làm mọi cảnh báo cũ bị dời vị trí | Dấu vân tay không dùng số dòng |
| Pull request không build được, SpotBugs không chạy được | Ghi rõ công cụ nào đã chạy. Semgrep và agent vẫn chạy |
| Agent báo file hoặc dòng không tồn tại | Script kiểm tra JSON, file, dòng và CWE. Kết quả sai bị loại và ghi log |
| Báo cáo của agent lệch dòng so với công cụ | Coi là trùng nếu cùng file, cùng hàm và cùng họ CWE |
| Công cụ hoặc LLM lỗi, quá thời gian | Stage quét không làm hỏng build. Comment ghi rõ phần nào chưa chạy |
| Chi phí vượt mức | Đặt giới hạn thời gian và tiền cho mỗi pull request |
| Quét chậm | Lưu kết quả của nhánh chính theo commit. Cập nhật cơ sở dữ liệu lỗ hổng theo lịch riêng. Chỉ quét thư viện khi `pom.xml` hoặc file Gradle thay đổi |
| Mã sinh tự động, thư mục build, file quá lớn | Bỏ qua theo danh sách cấu hình |
| Mã test | Hạ mức ưu tiên, không bỏ hẳn |
| Pull request quá lớn | Comment báo rõ chỉ phân tích được một phần |

### 7.7. Môi trường

- **Phát triển:** Jenkins chạy bằng Docker trên máy local. Chưa cần máy chủ thật.
- **Công cụ:** đóng gói trong một Docker image chung để mọi thành viên chạy giống nhau.
- **Viết script:** chạy trực tiếp trên file kết quả quét, không cần đợi Jenkins.
- **Thực nghiệm:** chạy hàng loạt bằng script Python, không qua Jenkins.
- **Demo:** chạy trên bản fork của một dự án Java mã nguồn mở, có video dự phòng.

## 8. Thiết kế thực nghiệm

### 8.1. Dữ liệu

| Dữ liệu | Mục đích | Nguồn đáp án |
|---|---|---|
| OWASP Benchmark, WebGoat | Kiểm tra quy trình và đo công cụ theo từng loại lỗi | Đáp án có sẵn, lỗ hổng cài cố ý |
| **Pull request có lỗi** (mục tiêu 40–60) | Đo khả năng tìm lỗi | CVE và commit sửa lỗi |
| **Pull request đối chứng** (mục tiêu 40–60) | Đo báo động giả | Bản đã vá và pull request bình thường |
| Pull request của công ty Z (tạm gác) | Đánh giá triển khai | Hành động và xác nhận của lập trình viên |

**Cách tạo pull request có lỗi:**

1. Chọn CVE Java có commit sửa lỗi từ Vul4J (79 lỗ hổng, 51 dự án) [5] và Project KB (624 lỗ hổng, 205 dự án Java) [6].
2. Chọn thay đổi nhỏ, nằm trong mã tự viết và thuộc các loại CWE đã định trước.
3. Đảo ngược commit sửa lỗi để tạo pull request đưa lỗi vào.
4. Bỏ test, nội dung commit, mã CVE và mọi chi tiết lộ đáp án.
5. Kiểm tra pull request build được. Nếu không, báo cáo riêng nhóm này, vì SpotBugs không chạy được trên đó.

**Pull request đối chứng** gồm chính thay đổi sửa lỗi, kèm các pull request bình thường lấy từ cùng dự án.

Nhóm cần kiểm tra thêm giấy phép, và lưu ý README của Vul4J cho biết một số lỗ hổng không còn tái hiện được.

### 8.2. Bốn cách so sánh

| Cách | Luồng | Mạnh | Yếu |
|---|---|---|---|
| A. Chỉ công cụ | Quét, lọc bằng script, xếp ưu tiên | Nhanh, ổn định, chi phí thấp | Nhiều nhiễu, khó thấy lỗi logic |
| B. Công cụ + LLM lọc | Cách A, rồi LLM loại báo sai | Ít nhiễu hơn | Không tìm thêm được lỗi mới |
| C. Agent đọc pull request | Agent đọc thay đổi và repo | Có thể thấy lỗi ngoài luật | Tốn kém, dao động, có thể tự nghĩ ra lỗi |
| D. Kết hợp | Agent nhận thêm cảnh báo của công cụ | Có thể mạnh nhất | Cần chứng minh bằng số liệu |

B, C và D dùng cùng một mô hình cloud để so sánh công bằng. Nếu kịp, chạy thêm B bằng LLM local, vì công ty có thể không cho gửi mã ra ngoài.

### 8.3. Chấm điểm

Một lỗi được coi là **tìm thấy** nếu báo cáo chỉ đúng file và hàm liên quan, đồng thời mô tả đúng nguyên nhân. Hai người chấm độc lập, không biết báo cáo đến từ cách nào.

| Nhóm | Chỉ số |
|---|---|
| Tìm lỗi | Tỉ lệ pull request có lỗi được tìm thấy, số lỗi chỉ một cách tìm ra |
| Báo động giả | Số báo cáo sai trên mỗi pull request, tỉ lệ pull request đối chứng bị báo động giả, precision |
| Lọc | Số lỗi thật bị cách B loại nhầm so với cách A |
| Độ ổn định | Mức khác nhau giữa các lần chạy |
| Kỹ thuật | Tỉ lệ kết quả agent bị script loại, tỉ lệ gộp sai trên một mẫu nhỏ |
| Chi phí | Thời gian và tiền cho mỗi pull request |

Mọi tỉ lệ đều kèm khoảng tin cậy 95%. Khi so sánh hai cách trên cùng bộ dữ liệu, nhóm dùng kiểm định theo cặp như McNemar.

### 8.4. Xác nhận báo cáo ngoài đáp án

Một cách có thể báo một lỗi đúng nhưng không nằm trong đáp án. Vì vậy các báo cáo ngoài đáp án cần người đọc lại:

1. Viết tiêu chí một trang cho các nhãn Đúng, Sai, Không chắc.
2. Lấy ngẫu nhiên khoảng 120–150 báo cáo bằng script, từ cả bốn cách.
3. Hai người gán nhãn độc lập, không biết nguồn của báo cáo.
4. Đo mức đồng thuận bằng Cohen's kappa và thảo luận các trường hợp bất đồng.

Nên chia bộ pull request thành phần phát triển và phần đánh giá. Chỉ chỉnh prompt trên phần phát triển.

Công cụ AI được dùng để viết code nhưng không được dùng để tạo đáp án hay nhãn. Dự kiến 20–40 giờ công cho 120 báo cáo.

### 8.5. Các nguy cơ với độ tin cậy của kết quả

- **Mô hình nhớ CVE cũ:** LLM có thể đã biết các lỗ hổng công khai này, nên kết quả có thể cao hơn thực tế. Nhóm tắt internet khi chạy, bỏ chi tiết nhận dạng, và ưu tiên thêm CVE công bố gần đây.
- **Pull request tạo ra không hoàn toàn giống thật:** đảo ngược commit sửa lỗi không giống cách lỗi được đưa vào ban đầu.
- **Đối chứng không chắc sạch lỗi:** pull request bình thường có thể có lỗi chưa ai biết, nên báo cáo trên đó phải được người đọc lại.
- **Mẫu nhỏ và chọn lọc:** chỉ vài chục pull request, nên kết quả không đại diện cho mọi loại lỗi.

### 8.6. Tái lập

Ghi lại phiên bản công cụ, mô hình, ngày chạy và toàn bộ prompt. Mỗi pull request được chạy LLM và agent ít nhất 3 lần. Công khai bộ pull request và script đánh giá.

## 9. Triển khai tại công ty Z

**Phần này đang tạm gác.** Nhóm hoàn thành RQ1–RQ3 và demo trước. Mục này ghi lại phương án để dùng khi quay lại.

**Các mức hợp tác**, vì thông tin của công ty thường không được mang ra ngoài:

| Mức | Cách làm | Dữ liệu ra khỏi công ty |
|---|---|---|
| 1. Nhóm chạy trong công ty | Thành viên làm ở công ty, hoặc người được cấp quyền, chạy quy trình | Bảng số liệu tổng hợp đã được duyệt |
| 2. Công ty tự chạy | Nhóm giao Docker image, kỹ sư công ty tự cài và chạy | Chỉ bảng tổng hợp do công ty gửi |
| 3. Dự án không nhạy cảm | Chạy trên công cụ nội bộ nhỏ hoặc dự án mã nguồn mở của công ty | Ít nhạy cảm, vẫn cần được duyệt |
| 4. Lập trình viên đánh giá trên mã công khai | Lập trình viên chấm báo cáo trên pull request mã nguồn mở | Chỉ có ý kiến |

Mức 2 là mục tiêu đề xuất. Mức 4 không đo được hành động thật, nên cần hỏi thầy xem có được chấp nhận không.

**Yêu cầu với công ty:** một nhóm dự án Java dùng Git, Jenkins và pull request hoặc merge request; được thêm stage chỉ comment trong ít nhất 2 tuần; một đến hai lập trình viên phản hồi; đồng ý công bố số liệu đã ẩn danh và xác nhận kết quả. Cần hỏi thêm Jenkins có nhận được webhook không.

**Cách đo RQ4:**

- Xếp mỗi báo cáo vào một trong bốn kết cục: Đã sửa, Có phản hồi nhưng chưa sửa, Bị bác bỏ, Bị bỏ qua.
- Thu thập tự động bằng nhật ký trong máy công ty, reaction hoặc lệnh `/false-positive`, và so sánh với lần quét cuối trước khi merge. Hai người đọc lại các trường hợp Đã sửa và Bị bỏ qua.
- Chi phí lấy từ log Jenkins và số token; thời gian xử lý lấy từ khảo sát cuối đợt.
- Mốc so sánh là kết quả chạy lại trên 20–30 pull request đã merge.

Chỉ công bố số tổng hợp, không nêu tên công ty, không công bố loại lỗi chưa sửa, và gộp các nhóm quá nhỏ. Nhóm dự án nhỏ chỉ có vài chục pull request trong 2 tuần, nên đây là nghiên cứu trường hợp, không phải kết luận tổng quát.

## 10. Đóng góp dự kiến

- **C1, đóng góp chính.** So sánh tái lập được giữa công cụ, LLM lọc, agent và cách kết hợp trên pull request Java có đáp án.
- **C2.** Bộ pull request có đáp án và khung đánh giá, công khai để người khác dùng lại.
- **C3.** Quy trình tích hợp Jenkins và comment trên pull request.
- **C4.** Số liệu triển khai trong doanh nghiệp, nếu có công ty.

**Triết lý khoa học:** cảnh báo chưa phải là lỗ hổng. LLM và agent chỉ đề xuất. Mỗi kết luận phải được kiểm bằng bằng chứng độc lập với nguồn đã sinh ra nó. Nếu agent không tốt hơn công cụ, đó vẫn là kết quả có giá trị và được báo cáo trung thực.

## 11. Đáp ứng yêu cầu đề tài

| Yêu cầu | Nội dung trong proposal | Còn thiếu |
|---|---|---|
| 1. Đọc bài, từ khóa, tài liệu | Mục 5 | Khảo sát kỹ các nghiên cứu về LLM trong review bảo mật |
| 2. RQ, khảo sát hiện trạng, quy trình, thử nghiệm | Mục 6, 7, 8 | Khảo sát hiện trạng tại công ty |
| 3. Đóng góp, triết lý, phương pháp đo | Mục 8, 10 | Chốt đóng góp sau khi khảo sát |
| 4. Báo cáo thực nghiệm đủ điều kiện arXiv | Mục 12, 14 | Số liệu thật |

Điểm A cần thấy hiệu quả ở công ty và có xác nhận. Trong khi phần công ty còn tạm gác, mục tiêu thực tế là điểm B. Hướng TT coi trọng triển khai ở công ty, nên nhóm cần hỏi thầy sớm xem việc gác lại có ảnh hưởng gì thêm không.

## 12. Kế hoạch

| Thời gian | Công việc | Kết quả |
|---|---|---|
| Đến 11/11 | Họp khởi động, hỏi thầy, khảo sát tài liệu. Dựng Jenkins Docker, làm thành phần 1, 2. Thử tạo 10 pull request từ CVE | Biết cách tạo dữ liệu có khả thi không, RQ bản chốt |
| 12–17/11 | Chương trình lõi, thành phần 3, 4, 6. Hoàn thiện bộ pull request. Chạy cách A | Kết quả RQ1 |
| **18–19/11** | **Báo cáo lần 1** | Xong nội dung 1 và 2 |
| 18–24/11 | Thành phần 5. Chạy cách B, C, D. Chấm điểm và gán nhãn. Viết phần đóng góp | Kết quả RQ2, RQ3 |
| **25–26/11** | **Báo cáo lần 2** | Xong nội dung 1–3 |
| Từ 27/11 | Thành phần 7, demo trên bản fork. Quay lại phần công ty nếu có điều kiện | Luồng pull request chạy được |
| 12/2026 | Viết báo cáo, bản arXiv, slide. Nộp và bảo vệ theo lịch của thầy | Hoàn thiện sản phẩm |

## 13. Phân công đề xuất

| # | Vai trò | Phụ trách | Viết code | Thành viên |
|---|---|---|---|---|
| 1 | Trưởng nhóm | Điều phối, làm việc với thầy và công ty, chủ trì báo cáo | Ít | |
| 2 | Tài liệu và trình bày | Khảo sát tài liệu, slide, báo cáo | Ít | |
| 3 | Jenkins và Git | Thành phần 1, 7, tích hợp Gitleaks | Nhiều | |
| 4 | Quét thư viện và dữ liệu CVE | Syft, Dependency-Check, OSV-Scanner, chọn CVE | Vừa | |
| 5 | Quét mã nguồn | SpotBugs + FindSecBugs, Semgrep, tiêu chí chấm theo CWE | Vừa | |
| 6 | Dữ liệu và đo lường | Thành phần 2, 3, 6, thống kê | Nhiều | |
| 7 | LLM và agent | Thành phần 4, 5, chạy các cách B, C, D | Nhiều | |

Mọi thành viên cùng tham gia chấm điểm và gán nhãn.

## 14. Sản phẩm

Báo cáo đầy đủ, báo cáo tóm tắt dạng bài báo, slide, tài liệu hướng dẫn, mã nguồn, bộ pull request đánh giá và số liệu đã ẩn danh.

## 15. Rủi ro

| Rủi ro | Cách giảm |
|---|---|
| Tạo bộ pull request mất nhiều thời gian | Thử 10 pull request trong tuần đầu; giảm số lượng nếu cần, nhưng giữ chất lượng đáp án |
| Không có công ty nên khó đạt điểm A | Hỏi thầy sớm; RQ1–RQ3 không phụ thuộc công ty; giữ sẵn các mức hợp tác ở mục 9 |
| CVE cũ không build lại được | Kiểm tra sớm trong 10 pull request thử; báo cáo riêng nhóm không build được |
| Chi phí agent cao | Đặt ngân sách trước, đo trên mẫu nhỏ trước khi chạy toàn bộ |
| Khối lượng quá lớn | Làm theo các mức ở mục 4 |
| Đã có nghiên cứu trùng với đóng góp chính | Khảo sát ngay tuần đầu, điều chỉnh góc nhìn nếu cần |
| Kết quả bị thổi phồng vì mô hình nhớ CVE | Thực hiện các biện pháp ở mục 8.5 và nêu rõ trong báo cáo |
| Lộ dữ liệu qua repo public | Kết quả thô ngoài git, không đưa tên công ty và mã nội bộ lên repo |

## 16. Cần nhóm quyết định

1. Có đồng ý đóng góp chính ở mục 1 không?
2. Có đồng ý các ngưỡng ở mục 3 không?
3. Dùng mô hình và agent cloud nào, ngân sách bao nhiêu, ai có tài khoản?
4. Tập trung vào những loại CWE nào?
5. Ai nhận vai trò nào?

**Cần hỏi thầy:** nếu tạm gác phần công ty thì mức điểm bị ảnh hưởng thế nào; xác nhận của công ty theo hình thức nào; dự án mã nguồn mở có được thay cho công ty không.

## Tài liệu tham khảo

[1] R. Idan, T. Cohen Galor, A. Shabtai, and Y. Elovici, "An empirical security analysis of open-source software used in onboard satellite systems," arXiv:2609.15425, Sep. 2026.

[2] C. Wang, Z. Li, S. Dutta, and M. Naik, "QLCoder: A query synthesizer for static analysis of security vulnerabilities," in *Proc. Int. Conf. Learning Representations (ICLR)*, 2026, arXiv:2511.08462.

[3] F. Fleischer và cộng sự, "Contextualizing sink knowledge for Java vulnerability discovery," arXiv:2604.01645, 2026.

[4] M. Iranmanesh và cộng sự, "P2Patch: Exploit-guided vulnerability repair," arXiv:2610.20245, Oct. 2026.

[5] Q.-C. Bui, R. Scandariato, and N. E. Díaz Ferreyra, "Vul4J: A dataset of reproducible Java vulnerabilities geared towards the study of program repair techniques," in *Proc. Int. Conf. Mining Software Repositories (MSR)*, 2022. https://github.com/tuhh-softsec/vul4j

[6] S. E. Ponta, H. Plate, A. Sabetta, M. Bezzi, and C. Dangremont, "A manually-curated dataset of fixes to vulnerabilities of open-source software," in *Proc. Int. Conf. Mining Software Repositories (MSR)*, 2019, arXiv:1902.02595. https://github.com/sap/project-kb

[7] Sourcegraph, "Lessons from building Sherlock: Automating security code reviews with Sourcegraph." https://sourcegraph.com/blog/lessons-from-building-sherlock-automating-security-code-reviews-with-sourcegraph

[8] Datadog, "AI-Enhanced SAST." https://docs.datadoghq.com/security/code_security/static_analysis/ai_enhanced_sast/
