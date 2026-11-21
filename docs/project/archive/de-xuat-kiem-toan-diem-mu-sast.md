# Kiểm toán điểm mù SAST bằng lỗ hổng gieo trên mã của công ty Z

## 1. Tóm tắt

Đề xuất trả lời một câu hỏi: **công cụ quét bảo mật mà công ty Z đang dùng bỏ sót những loại lỗ hổng nào trên chính mã của Z?**

1. Một LLM agent gieo lỗ hổng có kiểm soát vào một bản sao sandbox của repo của Z. Nhóm không push lỗ hổng gieo lên repo của Z.
2. Nhóm chạy công cụ SAST hiện có của Z trên bản có lỗ hổng và trên bản gốc. Một lỗ hổng tính là bắt được khi công cụ báo một cảnh báo mới tại vị trí gieo.
3. Từ đó nhóm lập bản đồ điểm mù. Bản đồ này là recall, tức tỉ lệ lỗ hổng mà công cụ bắt được, tính theo từng loại lỗi (CWE) và từng mức khó.
4. Nhóm sinh luật Semgrep để lấp điểm mù, rồi chấm luật trên các lỗ hổng do kỹ sư Z tự gieo mà nhóm không biết trước.

Nhóm biết trước vị trí của mọi lỗ hổng vì chính nhóm gieo chúng. Nhờ vậy Z không phải gán nhãn cảnh báo và không phải mở luồng pull request. Phần việc của Z là khoảng 3 giờ của một tech lead.

## 2. Vì sao cần đo phần công cụ bỏ sót

Nhiều nghiên cứu về công cụ SAST đo precision, tức trong những gì công cụ đã báo thì bao nhiêu là đúng. Bài phân tích phần mềm vệ tinh ước lượng 22,2% cảnh báo là báo sai sau khi đã làm sạch dữ liệu [1]. Hai công trình năm 2026 dùng LLM để lọc báo sai. Một bài nhận ra tới 93,3% cảnh báo sai của CodeQL [10]. Bài còn lại loại được 94% đến 98% cảnh báo sai trên dữ liệu công nghiệp của Tencent [11].

Theo những gì nhóm tìm được, câu hỏi ngược lại ít được đo trên mã doanh nghiệp: công cụ bỏ sót gì? Li và cộng sự cho thấy 7 công cụ SAST Java chỉ bắt được 12,7% CVE thật [5]. Con số đó đo trên mã nguồn mở. Nó không cho doanh nghiệp biết công cụ của họ mù ở đâu trên framework, helper và quy ước riêng của họ.

Khi công cụ im lặng trên một module, nhóm phát triển cần biết module đó an toàn hay công cụ không nhìn thấy loại lỗi đó. Doanh nghiệp cần câu trả lời này trước khi tin vào cổng bảo mật trong CI.

Trên mã độc quyền, không ai biết hết lỗ hổng thật, nên không có đáp án để tính recall. Lỗ hổng gieo là cách rẻ nhất để có đáp án. Nhóm biết chính xác lỗi nằm ở đâu, vì chính nhóm đặt lỗi vào.

## 3. Quy trình

### 3.1. Các bước

1. **Khóa thí nghiệm.** Chọn 1 đến 3 repo của Z và khóa commit gốc. Ghi lại phiên bản và cấu hình của từng công cụ.
2. **Lập danh mục loại lỗi.** Chọn 6 đến 8 CWE theo stack của Z. Ví dụ với web service: CWE-89, CWE-78, CWE-22, CWE-502, CWE-601, CWE-918, CWE-862, CWE-639.
3. **Chọn vị trí gieo.** Script tìm các lời gọi sink, tức API nguy hiểm như truy vấn SQL, `exec`, thao tác file, giải tuần tự hóa. LLM giữ lại các vị trí mà dữ liệu từ ngoài có thể đi tới.
4. **Gieo lỗ hổng.** Agent sửa mã tại từng vị trí để đưa vào một lỗ hổng của một CWE, ở một trong ba mức khó (mục 3.2). Mỗi lỗ hổng gieo là một patch riêng trên commit gốc.
5. **Kiểm tra lỗ hổng gieo có hợp lệ.** Một lỗ hổng gieo hợp lệ khi đạt cả ba điều kiện:
   - mã build được và test hiện có vẫn pass;
   - có test PoV, tức một test chạy được để chứng minh lỗi tồn tại, hoặc có 2 người xác nhận độc lập;
   - người kiểm tra không phải người viết prompt gieo lỗi.
6. **Quét.** Chạy từng công cụ trên bản gốc và trên từng bản có lỗ hổng.
7. **Chấm.** Một lỗ hổng tính là bắt được khi công cụ báo một cảnh báo có trên bản gieo, không có trên bản gốc, và nằm trong hàm chứa đoạn mã gieo. Nhóm ghi riêng một cột cho biết CWE của cảnh báo có khớp với CWE đã gieo không.
8. **Sinh luật.** LLM viết luật Semgrep cho các điểm mù, chỉ dùng tập `dev`. LLM sửa luật qua nhiều vòng theo kết quả chạy luật, như QLCoder [2].
9. **Chấm luật.** Chạy luật trên tập `held-out` để đo recall, và trên HEAD sạch của Z để đo báo sai.

### 3.2. Ba mức khó

| Mức | Mô tả | Ví dụ |
|---|---|---|
| L1, cục bộ | Nguồn dữ liệu và sink nằm trong cùng một hàm | Tham số request được ghép thẳng vào câu SQL |
| L2, qua helper nội bộ | Dữ liệu đi qua ít nhất một hàm hoặc file nội bộ của Z trước khi tới sink | Tham số đi qua `buildFilter()` của Z rồi vào câu SQL |
| L3, logic và quyền | Không có sink cú pháp rõ ràng | Xóa một dòng kiểm tra quyền sở hữu trước khi trả bản ghi |

Giả thuyết chính nằm ở L2. Công cụ mặc định biết các API chuẩn, nhưng không biết helper riêng của Z.

### 3.3. Tách oracle

Bài P2Patch chỉ ra rằng bằng chứng dùng để tạo kết quả không được dùng lại để chấm kết quả đó [4]. Đề xuất áp dụng nguyên tắc này theo ba cách:

- Nhóm chia tập `dev` và tập `held-out` theo kiểu biến đổi và theo file, không chia ngẫu nhiên từng mẫu. Cách chia này ngăn luật học thuộc văn phong của bộ gieo.
- Tập `held-out` có 10 đến 20 lỗ hổng do kỹ sư Z và các thành viên không viết luật gieo bằng tay. Người viết luật không thấy các lỗ hổng này.
- Nhóm gắn tag Git cho prompt và luật trước khi chạy trên `held-out`.

## 4. Liên hệ với các công trình nền tảng

| Bài | Phần nhóm dùng |
|---|---|
| Bài vệ tinh [1] | Pipeline nhiều công cụ, chuẩn hóa, dấu vân tay, khoảng tin cậy Wilson, phân tích độ nhạy theo từng công cụ. Bài này đo precision. Đề xuất bổ sung phía recall mà bài không đo |
| QLCoder [2] | Tiêu chí "báo trên bản lỗi, im lặng trên bản gốc" để chấm phát hiện. Vòng sinh luật có phản hồi từ việc chạy luật |
| GONDAR [3] | Chọn vị trí gieo theo sink và theo việc dữ liệu từ ngoài có đi tới được không |
| P2Patch [4] | Tách oracle (mục 3.3). Nếu còn thời gian, nhóm thêm vòng đối kháng, trong đó một agent viết biến thể tương đương ngữ nghĩa để vượt qua luật (RQ4) |

## 5. Câu hỏi nghiên cứu

| RQ | Câu hỏi | Giả thuyết có thể bác bỏ | Dữ liệu |
|---|---|---|---|
| RQ1 Hiện trạng | Công cụ SAST của Z bỏ sót những loại lỗi nào, ở mức khó nào? | Recall ở L2 không quá một nửa recall ở L1. Nếu hai mức gần bằng nhau, giả thuyết "điểm mù nằm ở helper nội bộ" bị bác | 100 đến 150 lỗ hổng gieo hợp lệ trên mỗi repo |
| RQ2 Độ tin cậy của phép đo | Recall đo trên lỗ hổng do LLM gieo có phản ánh recall trên lỗi do người gieo và lỗi thật không? | Ít nhất 70% lỗ hổng gieo hợp lệ. Thứ hạng recall theo CWE trên lỗ hổng LLM gieo tương quan với thứ hạng trên lỗi do người gieo và 20 cặp CVE thật, Kendall τ ≥ 0,5 | Lỗ hổng LLM gieo, 10 đến 20 lỗi do người gieo, 20 cặp CVE cùng ngôn ngữ |
| RQ3 Lấp điểm mù | Luật sinh từ tập `dev` tăng recall trên tập `held-out` bao nhiêu, và báo sai bao nhiêu trên mã sạch? | Recall trên `held-out` tăng ít nhất 20 điểm phần trăm. Ít nhất 50% cảnh báo của luật mới trên HEAD sạch của Z là đúng. Nếu không đạt, luật đang học thuộc lỗ hổng gieo | Tập `held-out`, HEAD của 1 đến 3 repo |
| RQ4 (nếu kịp) Độ bền | Bao nhiêu luật bị biến thể tương đương ngữ nghĩa vượt qua? | Ít nhất 30% luật bị vượt trong tối đa 3 lần thử. Sau một vòng sửa luật, tỉ lệ này dưới 15% và recall trên `held-out` không giảm | Agent tấn công, luật phiên bản r0 và r1 |

**RQ2 quyết định giá trị của RQ1 và RQ3.** Li và cộng sự đã phê phán benchmark dùng lỗ hổng tiêm vào là thiếu thực tế [5]. Nếu không trả lời RQ2, người đọc có thể bác mọi con số của RQ1 và RQ3 bằng lập luận đó. Nếu RQ2 cho kết quả âm, nhóm báo cáo kết quả âm đó làm phát hiện chính. Khi đó kết luận là lỗ hổng do LLM gieo chưa dùng được để kiểm toán công cụ trên mã doanh nghiệp.

RQ1 cũng là phần khảo sát hiện trạng tại Z. Phần này có thêm một buổi phỏng vấn 30 phút với tech lead của Z về công cụ, cấu hình và quy trình hiện tại.

## 6. Đóng góp và triết lý

**Đóng góp dự kiến:**

- **C1.** Giao thức kiểm toán recall của SAST trên mã doanh nghiệp, có đáp án theo cách xây dựng và có kiểm định độ tin cậy của phép đo (RQ2).
- **C2.** Bản đồ điểm mù trên mã của một doanh nghiệp phần mềm Việt Nam, có công ty xác nhận.
- **C3.** Số liệu cho biết luật do LLM sinh có bắt được lỗi ngoài tập `dev` không, khi chấm bằng oracle tách biệt.
- **C4.** Bộ script kiểm toán mã nguồn mở để doanh nghiệp khác chạy lại.

**Triết lý khoa học:**

- Công cụ im lặng không có nghĩa là mã an toàn. Doanh nghiệp cần biết công cụ bỏ sót gì thì mới chọn được công cụ nên đầu tư.
- Một phép đo dùng dữ liệu nhân tạo phải tự chứng minh độ tin cậy của nó. Vì vậy nhóm trả lời RQ2 trước khi kết luận từ RQ1 và RQ3.
- Bằng chứng tạo ra kết quả không được dùng để chấm chính kết quả đó.
- Kết quả âm vẫn được báo cáo đầy đủ.

## 7. Triển khai tại công ty Z

### 7.1. Yêu cầu với Z

| Việc | Thời gian của Z |
|---|---|
| Cung cấp danh sách công cụ và cấu hình SAST hiện tại | 20 phút |
| Phỏng vấn hiện trạng | 30 phút |
| Một kỹ sư gieo 5 đến 10 lỗi bằng tay theo hướng dẫn một trang, không cho nhóm xem | 60 phút |
| Duyệt bản đồ điểm mù và bộ luật đề xuất | 60 phút |
| Ký thư xác nhận | 10 phút |

Z có hai cách hợp tác:

1. Z cấp quyền cho một thành viên chạy bộ script kiểm toán trong hạ tầng của Z.
2. Z tự chạy container của nhóm, rồi gửi lại bảng recall đã ẩn danh.

Trong cả hai cách, mã nguồn, lỗ hổng gieo và kết quả thô không rời khỏi Z. Lỗ hổng chỉ nằm trong bản sao sandbox, và nhóm xóa bản sao đó sau thí nghiệm. Nhóm chỉ gửi mã lên LLM cloud khi Z đồng ý bằng văn bản. Nếu không có đồng ý đó, nhóm dùng mô hình chạy cục bộ.

### 7.2. Cách đo hiệu quả

Con số chính có dạng: trên N lỗi do kỹ sư Z tự gieo, **công cụ của Z bắt được x lỗi trước khi thêm bộ luật và y lỗi sau khi thêm bộ luật.** Oracle này độc lập, vì nhóm không thấy các lỗi đó trước khi chấm.

Các chỉ số đi kèm:

- số luật Z chấp nhận đưa vào CI ở chế độ chỉ cảnh báo;
- số phát hiện thật trên HEAD do luật mới tìm ra, có kỹ sư Z xác nhận;
- thời gian CI tăng thêm;
- số giờ công cho một lần kiểm toán.

### 7.3. Nếu không có Z

Nhóm kiểm toán 2 đến 3 ứng dụng mã nguồn mở cùng stack mà Z khai báo, ví dụ Spring PetClinic cho Java hoặc một ứng dụng Flask hay Django cho Python. Các thành viên không viết luật đóng vai kỹ sư Z và gieo lỗi bằng tay. RQ1 đến RQ3 vẫn trả lời được, nhưng kết quả không có xác nhận của công ty và không đo được hiệu quả tại doanh nghiệp.

## 8. Phạm vi

| Mức | Nội dung |
|---|---|
| Phải có | Bộ script gieo, quét và chấm. 6 đến 8 CWE, 3 mức khó. RQ1, RQ2, RQ3 trên ít nhất 1 repo |
| Nên có | 2 đến 3 repo, thêm một công cụ SAST thứ hai để so sánh, mô hình cục bộ |
| Nếu kịp | RQ4, CodeQL trên repo mã nguồn mở thay thế |
| Không làm | Viết công cụ quét mới, train mô hình, fuzzing, khai thác hệ thống đang chạy của Z, push lỗ hổng gieo lên repo của Z |

## 9. Công cụ

| Stack | SAST |
|---|---|
| Java | Semgrep CE, SpotBugs + FindSecBugs |
| Python | Semgrep CE, Bandit |
| Mọi stack | Công cụ Z đang dùng, nếu có |

Một số giới hạn của công cụ ảnh hưởng tới thiết kế:

- Semgrep CE chỉ theo dõi taint trong phạm vi một file. Theo dõi taint xuyên file cần bản trả phí, nên Semgrep CE nhiều khả năng bỏ sót lỗi L2 xuyên file. Nhóm phải kiểm lại chi tiết này trong tài liệu Semgrep trước khi chốt giả thuyết RQ1.
- Nhóm phải kiểm tra giấy phép CodeQL trước khi chạy trên mã thương mại của Z. Nếu giấy phép không cho phép, CodeQL chỉ chạy trên repo mã nguồn mở thay thế.
- SpotBugs cần build ra bytecode, nên mỗi bản gieo Java phải compile lại. Nếu repo của Z lớn, nhóm chọn một module nhỏ.

Nhóm dùng các phương pháp thống kê sau:

- khoảng tin cậy Wilson 95% cho mọi tỉ lệ;
- McNemar khi so recall trước và sau bộ luật trên cùng tập lỗi;
- Kendall τ cho RQ2;
- Cohen's κ cho bước xác nhận lỗ hổng hợp lệ.

**Cỡ mẫu.** Với 120 lỗ hổng hợp lệ và recall quanh 50%, khoảng tin cậy rộng khoảng ±9 điểm phần trăm. Chia thành 8 CWE × 3 mức thì mỗi ô chỉ có khoảng 5 mẫu, nên báo cáo theo từng CWE hoặc theo từng mức, không báo theo từng ô.

## 10. Kế hoạch và chia việc

| Thời gian | Việc | Kết quả |
|---|---|---|
| 08 đến 11/11 | Gửi Z email và gọi 30 phút. Chốt CWE, repo và repo mã nguồn mở thay thế. Cài sẵn công cụ trong một Docker image | Danh mục CWE, image chạy được |
| 12 đến 17/11 | Gieo phiên bản 1, xác nhận lỗ hổng hợp lệ, chạy RQ1 trên repo thay thế và trên repo của Z nếu có quyền | Bản đồ điểm mù sơ bộ |
| 18 đến 24/11 | Thu lỗi do người gieo, chạy RQ2. Sinh luật trên `dev`, chấm trên `held-out` (RQ3) | Số liệu RQ2, RQ3 |
| 27/11 đến 12/2026 | Bộ luật chạy ở chế độ cảnh báo trên HEAD của Z, Z duyệt, xin thư xác nhận. RQ4 nếu kịp. Viết bản arXiv, báo cáo đầy đủ, slide | Sản phẩm nộp |

| # | Phụ trách | Không được làm |
|---|---|---|
| 1 | Trưởng nhóm, đầu mối với Z, danh mục CWE | |
| 2 | Agent gieo lỗ hổng. Chọn sink, gieo theo 3 mức, kiểm tra build và test | Xác nhận lỗ hổng hợp lệ |
| 3 | Xác nhận lỗ hổng hợp lệ. Viết test PoV, điều phối 2 người xác nhận | Viết prompt gieo |
| 4 | Script quét, chuẩn hóa, so khớp cảnh báo với vị trí gieo | |
| 5 | Sinh luật Semgrep trên tập `dev` | Xem tập `held-out` |
| 6 | Thống kê, RQ4 nếu kịp | |
| 7 | Khảo sát tài liệu, hướng dẫn gieo bằng tay, báo cáo và slide | |

Thành viên 1, 6 và 7 gieo lỗi bằng tay cho tập `held-out` cùng kỹ sư Z.

## 11. Rủi ro

| Rủi ro | Cách giảm |
|---|---|
| Lỗ hổng gieo bị coi là nhân tạo, không đại diện cho lỗi thật | RQ2 đo trực tiếp vấn đề này bằng lỗi do người gieo và CVE thật. Kết quả âm vẫn được báo cáo |
| RQ1 cho kết quả hiển nhiên, ví dụ "Semgrep CE không bắt taint xuyên file" | Chốt giả thuyết sau khi đọc tài liệu công cụ. Đóng góp nằm ở bản đồ trên mã của Z và ở RQ2, không nằm ở riêng con số L2 |
| Z chưa dùng công cụ SAST nào | Đo bộ luật mặc định của Semgrep CE và nói rõ đây là mức cơ sở |
| Z e ngại việc gieo lỗ hổng vào mã của mình | Chỉ dùng bản sao sandbox, Z có thể tự chạy container, có biên bản xóa dữ liệu sau thí nghiệm |
| Cài công cụ và build mất thời gian | Đóng gói Docker image trong tuần đầu. Ưu tiên Python hoặc module Java nhỏ |
| Luật học thuộc văn phong của bộ gieo | Chia `dev` và `held-out` theo kiểu biến đổi, `held-out` có lỗi do người gieo |

## 12. Mức độ mới

Từng phần của đề xuất đều đã có người làm. Nhóm không được viết là "đầu tiên dùng mutation để đánh giá SAST".

| Công trình | Đã làm | Khác biệt của đề xuất |
|---|---|---|
| μSE, USENIX Security 2018 [6] | Đánh giá soundness của SAST Android bằng mutation | Mã doanh nghiệp, lỗ hổng do LLM gieo, kiểm định độ tin cậy của phép đo |
| Li và cộng sự, FSE 2023 [5] | 7 công cụ SAST Java chỉ bắt 12,7% CVE thật, phê phán benchmark dùng lỗ hổng tiêm vào | Đề xuất dùng lập luận này làm RQ2 thay vì né tránh |
| AVIATOR [7] | LLM agent gieo lỗ hổng để tạo dữ liệu huấn luyện | Dùng lỗ hổng gieo để kiểm toán công cụ, không để huấn luyện |
| arXiv:2603.17974 [8] | Đề cương tiến sĩ về gieo lỗ hổng mức repo kèm PoV | Chưa có đánh giá SAST, chưa triển khai ở doanh nghiệp. Nhóm mới đọc qua đoạn trích tìm kiếm, phải đọc bản gốc |
| QLCoder [2], Autogrep [9] | Sinh luật từ cặp bản lỗi và bản vá | Sinh luật từ lỗ hổng gieo, chấm trên lỗi do người gieo |

Phần còn lại cho nhóm gồm ba điểm:

1. Kiểm toán recall trên mã độc quyền, có công ty xác nhận.
2. Kiểm định lỗ hổng do LLM gieo có thay được lỗi thật không (RQ2).
3. Chuỗi gieo, sinh luật và chấm bằng oracle tách biệt.

Bảng trên đến từ một vòng tìm kiếm có AI hỗ trợ. Một công trình không có trong bảng nghĩa là nhóm chưa tìm thấy, không phải đã chứng minh là không có.

## 13. Cần quyết định

**Nhóm:**

1. Có chọn hướng này không?
2. Z dùng stack nào? Câu trả lời quyết định danh mục CWE và công cụ.
3. Có máy chạy mô hình cục bộ không, nếu Z không cho dùng LLM cloud?

**Hỏi Z:**

1. Z đang dùng công cụ SAST nào, cấu hình ra sao?
2. Có được chạy bộ script kiểm toán trên bản sao của 1 đến 3 repo không?
3. Có một kỹ sư dành khoảng 3 giờ trong tháng 11 không?
4. Có được gửi mã lên LLM cloud không?

## Tài liệu tham khảo

[1] R. Idan, T. Cohen Galor, A. Shabtai, and Y. Elovici, "An empirical security analysis of open-source software used in onboard satellite systems," arXiv:2609.15425, Sep. 2026.

[2] C. Wang, Z. Li, S. Dutta, and M. Naik, "QLCoder: A query synthesizer for static analysis of security vulnerabilities," in *Proc. ICLR*, 2026, arXiv:2511.08462.

[3] F. Fleischer et al., "Contextualizing sink knowledge for Java vulnerability discovery," arXiv:2604.01645, 2026.

[4] M. Iranmanesh et al., "P2Patch: Exploit-guided vulnerability repair," arXiv:2610.20245, Oct. 2026.

[5] K. Li et al., "Comparison and evaluation on static application security testing (SAST) tools for Java," in *Proc. ESEC/FSE*, 2023. https://sen-chen.github.io/img_cs/pdf/fse2023-sast.pdf

[6] R. Bonett, K. Kafle, K. Moran, A. Nadkarni, and D. Poshyvanyk, "Discovering flaws in security-focused static analysis tools for Android using systematic mutation," in *Proc. USENIX Security*, 2018, arXiv:2102.06823.

[7] AVIATOR, arXiv:2508.20866. https://arxiv.org/html/2508.20866v5 (cần kiểm tra lại tên tác giả và tiêu đề)

[8] arXiv:2603.17974, Mar. 2026. https://arxiv.org/abs/2603.17974 (mới đọc qua đoạn trích, cần kiểm tra lại)

[9] LambdaSec, "Autogrep: Automated generation and filtering of Semgrep rules from vulnerability patches." https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/

[10] Y. Xiong and T. Zhang, "Sifting the noise: A comparative study of LLM agents in vulnerability false positive filtering," in *Proc. ISSTA*, 2026, arXiv:2601.22952.

[11] X. Du et al., "Reducing false positives in static bug detection with LLMs: An empirical study in industry," in *Proc. ICSE-SEIP*, 2026, arXiv:2601.18844.
