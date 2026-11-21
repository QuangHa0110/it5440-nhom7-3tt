# Proposal đề tài Nhóm 7

**Kiểm chứng độc lập các sản phẩm demo web được dùng để quảng bá khóa học AI: quan sát thụ động, khả năng truy cập mã nguồn và quét tĩnh an toàn**

Tên tiếng Anh dự kiến: *Independent Auditability of Web Demonstrations Used in AI-Course Promotion: Passive Observation, Source Availability, and Safe Static Analysis*

| | |
|---|---|
| Học phần | IT5440 Nguyên lý và kỹ thuật phân tích chương trình, học kỳ 2026.1 |
| Nhóm | Nhóm 7, 7 học viên |
| Chủ đề liên hệ | Chương 11: Phân tích chương trình hướng bảo mật; có liên hệ Chương 15: Phân tích chương trình cho mã nguồn do trí tuệ nhân tạo sinh ra |
| Trạng thái | Bản nháp để nhóm duyệt trước khi thực hiện; cập nhật ngày 08/11/2026 |

## 1. Tóm tắt đề xuất

Một demo web có thể cho người xem thấy kết quả, nhưng không tự nó cho phép kiểm tra độc lập mã nguồn, dependency, quy trình xây dựng hay các rủi ro kỹ thuật. Điều này đặc biệt quan trọng khi demo được dùng công khai để quảng bá khóa học AI: người xem có thể muốn biết tuyên bố kỹ thuật nào được hỗ trợ bởi artifact công khai, và phần nào không thể kiểm chứng.

Đề tài xây dựng một quy trình kiểm chứng có giới hạn rõ ràng trên 10 sản phẩm demo web được liên kết trực tiếp từ trang, video hoặc tài liệu quảng bá công khai của khóa học AI. Quy trình có ba bước: quan sát thụ động demo bằng luồng giao diện bình thường và Inspector của trình duyệt; xác định có mã nguồn công khai clone được hay không; và quét tĩnh thụ động các repository đủ điều kiện. Đề tài chỉ báo cáo số liệu tổng hợp theo mã dự án, không nêu tên người, tài khoản, khóa học, URL repo hay bảng ánh xạ.

**Đóng góp chính:** một khung kiểm chứng tái sử dụng được để phân biệt (i) điều có thể quan sát từ demo, (ii) điều có thể kiểm tra từ artifact mã nguồn công khai, và (iii) điều không thể kết luận vì thiếu bằng chứng công khai.

**Nguyên tắc diễn giải:** thiếu mã nguồn không phải là bằng chứng dự án kém chất lượng; cảnh báo quét tĩnh không phải là bằng chứng có lỗ hổng khai thác được; và không kết quả nào là căn cứ để kết luận về năng lực, động cơ hay tính trung thực của một cá nhân. Nghiên cứu chỉ kiểm tra mức độ bằng chứng công khai hỗ trợ các tuyên bố kỹ thuật có thể kiểm chứng.

## 2. Vấn đề

Nhiều nội dung quảng bá chỉ dẫn tới một sản phẩm demo đang chạy. Người xem có thể quan sát giao diện, nhưng thường không biết mã nào tạo ra kết quả, dependency nào được dùng, có thể lấy phiên bản mã tương ứng hay không, và có tái tạo được các hành vi đã công bố hay không. Không có mã nguồn công khai thì không thể dùng phân tích chương trình để kiểm tra mã phía máy chủ; việc này là một giới hạn bằng chứng, không phải một phán quyết về sản phẩm.

Ngược lại, khi có repository công khai, chỉ đọc README cũng chưa đủ. Repository có thể thiếu lockfile, chứa dependency có lỗ hổng đã biết, để lộ chuỗi giống secret, hoặc có mẫu mã rủi ro mà công cụ phân tích tĩnh phát hiện. Các cảnh báo này cần được làm sạch, khử trùng lặp và kiểm tra thủ công. Nghiên cứu về 126 repository phần mềm vệ tinh cũng nhấn mạnh rằng kết quả công cụ phải được lọc theo phạm vi, khử trùng lặp và diễn giải là *findings*, không phải toàn bộ sự thật về khả năng khai thác [1].

Vấn đề thực tế là chưa có một quy trình nhỏ gọn, giới hạn dữ liệu cá nhân và không tấn công hệ thống, để trả lời đồng thời: demo công khai cho thấy được gì, artifact mã nguồn có sẵn đến đâu, và khi có mã nguồn thì các tín hiệu kỹ thuật nào xuất hiện. Quy trình này nhằm tạo cơ sở khách quan để đánh giá tuyên bố kỹ thuật; không nhằm truy tìm hay gán nhãn "phông bạt" cho bất cứ người nào.

## 3. Mục tiêu và tiêu chí thành công

Mục tiêu là thiết kế và thử nghiệm một quy trình kiểm chứng độc lập cho các demo web được quảng bá cùng khóa học AI, trong đó ranh giới giữa quan sát được, kiểm tra được và không thể xác minh được được ghi rõ.

Tiêu chí thành công đề xuất:

- Mỗi dự án được áp dụng cùng một rubric, có nhật ký quyết định và lý do loại trừ.
- Không thu thập hoặc công bố tên, tài khoản, email, ảnh, nội dung hồ sơ, doanh thu, thông tin liên hệ, nội dung học viên hay dữ liệu cá nhân khác.
- Mọi demo chỉ được quan sát qua luồng UI bình thường và Inspector; không đăng nhập, tạo tài khoản, dò endpoint, gửi request tùy biến, fuzzing hay vượt kiểm soát truy cập.
- Mọi repo đủ điều kiện được quét tĩnh cùng cấu hình đã chốt; không chạy ứng dụng, không cài dependency, không build bắt buộc và không sử dụng LLM/cloud để gửi mã nguồn.
- Báo cáo chỉ đưa ra số liệu tổng hợp và phân loại bằng chứng; không xếp hạng hay nêu danh tính dự án.
- Một người thứ hai, nếu có điều kiện, kiểm tra mù một mẫu tối thiểu 20% các quyết định mã hóa và xác minh cảnh báo.

Các ngưỡng cụ thể sẽ được chốt sau đợt pilot 2 dự án, ví dụ tỷ lệ dự án có artifact đủ điều kiện quét và tỷ lệ cảnh báo còn giữ lại sau xác minh. Không đặt trước ngưỡng để tạo ra một kết luận mong muốn.

## 4. Phạm vi

| Mức | Nội dung |
|---|---|
| **Phải có** | Tiêu chí lấy mẫu công khai, mã hóa ẩn danh, quan sát thụ động demo, kiểm tra khả năng clone, quét Semgrep, OSV-Scanner và Gitleaks ở chế độ thụ động, làm sạch và xác minh mẫu, báo cáo tổng hợp |
| **Nên có** | Kiểm tra độc lập 20% quyết định mã hóa; thống kê khoảng tin cậy; bộ dữ liệu tổng hợp không định danh và script xử lý |
| **Tạm gác** | So sánh với nhóm demo không gắn quảng bá khóa học; xác nhận trực tiếp với chủ dự án; kiểm tra tái lập/build/test |
| **Bỏ nếu thiếu thời gian** | Tạo SBOM riêng, bổ sung công cụ cho từng ngôn ngữ, phân tích lịch sử commit đầy đủ |
| **Không làm** | Thu thập hồ sơ cá nhân, đánh giá chất lượng khóa học hoặc hiệu quả nghề nghiệp, nêu tên dự án/người, quét xâm nhập, gửi payload tự tạo, fuzzing, khai thác lỗ hổng, đăng cảnh báo công khai, chạy mã đích, cài dependency hoặc gọi API không qua UI bình thường |

Đơn vị nghiên cứu là **sản phẩm demo/repository được quảng bá**, không phải con người. Chỉ xét tuyên bố kỹ thuật có thể kiểm chứng, chẳng hạn chức năng được demo, sự tồn tại của mã nguồn, hướng dẫn hoặc dependency. Không xét doanh thu, danh tiếng, năng lực, lời hứa nghề nghiệp hoặc động cơ marketing.

## 5. Cơ sở và khoảng trống nghiên cứu

| Nguồn | Đã làm được | Đề tài sử dụng |
|---|---|---|
| Nghiên cứu OSS cho hệ thống vệ tinh [1] | Phân tích 126 repo bằng SBOM, SCA, SAST, quét IaC và secret; làm sạch, lọc phạm vi, khử trùng lặp và xác minh mẫu | Mô hình nhiều nguồn, tách phát hiện tự động khỏi kết luận, dấu vết loại trừ và kiểm tra thủ công |
| QLCoder [2] | Sinh truy vấn CodeQL từ metadata CVE; đánh giá bằng bản lỗi và bản đã vá | Nguyên tắc đánh giá phải dùng bằng chứng phù hợp với câu hỏi, không coi một cảnh báo là kết luận cuối cùng |
| GONDAR [3] | Kết hợp lọc tĩnh với bằng chứng chạy thực tế để đánh giá khả năng khai thác | Lý do không suy diễn khả năng khai thác từ một tín hiệu tĩnh; đề tài này không chạy mã hay tạo exploit |
| P2Patch [4] | Tách bằng chứng tạo kết quả khỏi bộ bằng chứng đánh giá độc lập | Không dùng mô tả marketing hoặc chính cảnh báo công cụ như bằng chứng duy nhất cho kết luận |
| Tài liệu Semgrep [5], OSV-Scanner [6], Gitleaks [7] | Phân tích mẫu mã; đối chiếu dependency trong manifest/lockfile với cơ sở dữ liệu lỗ hổng; phát hiện chuỗi có dạng secret | Ba nguồn quét thụ động, chạy cục bộ, có phạm vi và giới hạn được nêu rõ |

Các bài [1]–[4] tập trung vào phân tích bảo mật và đánh giá công cụ trên phần mềm có mã nguồn. Chúng không trả lời trực tiếp câu hỏi một demo web công khai có tạo đủ điều kiện để kiểm chứng độc lập hay không. Ngược lại, các nghiên cứu về chất lượng mã do AI sinh thường giả định đã có mã nguồn để phân tích. Khoảng trống của đề tài là một quy trình coi **khả năng tiếp cận artifact** là kết quả đầu tiên: demo quan sát được, mã nguồn clone được và mã nguồn đủ điều kiện quét là ba mức bằng chứng khác nhau.

Đề tài không tuyên bố phát hiện một kỹ thuật quét mới. Đóng góp dự kiến là protocol lấy mẫu, rubric và cách diễn giải bảo thủ để kết nối quan sát demo với phân tích chương trình khi và chỉ khi source công khai tồn tại.

## 6. Câu hỏi nghiên cứu

| RQ | Câu hỏi | Dữ liệu và đơn vị phân tích |
|---|---|---|
| **RQ1** | Qua tương tác UI bình thường và Inspector, demo web công khai cho phép quan sát những bằng chứng kỹ thuật nào — request/response do trình duyệt tạo ra, kiểu dữ liệu, tài nguyên phía máy khách và lỗi hiển thị — và các bằng chứng đó hỗ trợ đến đâu cho tuyên bố chức năng công khai? | Bản ghi rubric tối thiểu của từng demo, chỉ giữ siêu dữ liệu kỹ thuật cần thiết |
  | **RQ2** | Mỗi demo có mã nguồn công khai clone được hay không; nếu không có, giới hạn kiểm chứng độc lập nằm ở đâu? | Trang/tài liệu quảng bá đã đáp ứng tiêu chí; trạng thái liên kết demo–repo; kết quả clone nông |
| **RQ3** | Trên các repository clone được, quét tĩnh thụ động đa công cụ phát hiện những nhóm tín hiệu kỹ thuật nào sau khi lọc, khử trùng lặp và xác minh? | Kết quả quét đã chuẩn hóa theo mã dự án và loại finding |
| **RQ4** | Khi gộp RQ1–RQ3, các sản phẩm demo được quảng bá cùng khóa học AI có thể được kiểm chứng độc lập đến đâu; điểm nghẽn chủ yếu là demo, truy cập mã nguồn hay artifact kỹ thuật? | Bảng tổng hợp ẩn danh trên toàn bộ mẫu |

RQ4 là câu hỏi tổng hợp. Nó không kiểm định một mệnh đề về con người và không được diễn giải thành quan hệ nhân quả giữa việc dùng AI với chất lượng hoặc an toàn phần mềm.

## 7. Giải pháp

### 7.1. Luồng kiểm chứng

```text
Trang/video/tài liệu quảng bá công khai của khóa học AI
  → kiểm tra tiêu chí đưa vào, gán mã P01…P40
  → quan sát demo qua UI bình thường và Inspector
  → phân loại có/không có liên kết mã nguồn công khai
  → clone nông repository nếu công khai và không cần xác thực
  → quét tĩnh thụ động tại máy cục bộ
  → chuẩn hóa, khử trùng lặp, xác minh theo rubric
  → chỉ xuất bảng tổng hợp ẩn danh và giới hạn diễn giải
```

Không có bước nào gọi API ngoài những request vốn do trình duyệt phát sinh trong luồng sử dụng bình thường. Không thử endpoint ẩn, tham số lạ, quyền truy cập khác, tài khoản, thanh toán hay dữ liệu của người dùng khác.

### 7.2. Tiêu chí lấy mẫu và loại trừ

Một mục được đưa vào khi thỏa tất cả điều kiện sau:

1. Có trang, video hoặc tài liệu **công khai** dùng để quảng bá một khóa học AI.
2. Nguồn quảng bá liên kết trực tiếp tới demo web hoặc mô tả đủ rõ sản phẩm demo cần quan sát.
3. Demo truy cập được không cần đăng nhập, mời riêng, thanh toán hoặc cung cấp dữ liệu cá nhân.
4. Tại thời điểm thu thập, việc quan sát trong trình duyệt không yêu cầu thao tác vượt ngoài sử dụng thông thường.

Loại trừ các mục không có demo xác định được, demo yêu cầu tài khoản/thanh toán, hệ thống liên quan đến y tế–tài chính–trẻ em hoặc dữ liệu nhạy cảm, và repo yêu cầu quyền truy cập. Một repo có thể được phát hiện từ demo, nhưng chỉ clone nếu URL công khai được liên kết rõ ràng từ demo hoặc tài liệu quảng bá; không tìm repo bằng suy đoán tên hay bằng hồ sơ cá nhân.

Mẫu được chọn tuần tự theo tiêu chí công khai cho tới khi đạt 10 mục đủ điều kiện, không chọn theo mức độ nổi tiếng, mức độ gây tranh cãi hoặc dự đoán trước về chất lượng. Bảng ánh xạ URL–mã P chỉ dùng nội bộ để tránh quét trùng; không đưa vào báo cáo hay dữ liệu phát hành, được truy cập hạn chế và xóa khi kết thúc học kỳ 2026.1.

### 7.3. Quan sát thụ động demo cho RQ1

Người nghiên cứu mở demo trong trình duyệt, dùng đúng luồng UI hiển nhiên và Inspector để ghi các trường rubric sau:

| Nhóm | Ghi nhận | Không ghi nhận/không làm |
|---|---|---|
| Tuyên bố chức năng | Chức năng kỹ thuật được trang quảng bá hoặc demo nêu rõ | Nhận xét về khả năng của tác giả hoặc giá trị thương mại |
| UI và đầu ra | Có/không quan sát được luồng chức năng đã nêu; loại dữ liệu vào/ra ở mức khái quát | Nội dung người dùng, prompt nhạy cảm, ảnh, tài khoản hoặc dữ liệu cá nhân |
| Network | Phương thức, mã trạng thái, loại tài nguyên, miền đích và schema ở mức cần thiết của request/response do UI tạo ra | Request tự tạo, quét endpoint, replay request, thay token/cookie hay thử bypass |
| Client | Có/không có source map, bundle, cấu hình công khai hoặc thông báo lỗi liên quan | Giải mã, obfuscation bypass hoặc cố tình làm lộ thông tin không hiển thị |
| Liên hệ artifact | Có đường dẫn source/release/tài liệu công khai từ demo hay không | Tìm danh tính hoặc repo qua công cụ tìm kiếm cá nhân |

Kết quả RQ1 chỉ có ba nhãn: **quan sát được**, **không quan sát được trong phạm vi cho phép**, và **ngoài phạm vi/không đủ bằng chứng**. Một lỗi hiển thị không được coi là lỗ hổng; nó chỉ là thông tin hạn chế về behavior quan sát được.

### 7.4. Kiểm tra source và quét tĩnh cho RQ2–RQ3

Repository đủ điều kiện được clone nông tại commit mặc định bằng HTTPS không xác thực. Không đọc hồ sơ người đóng góp, không phân tích lịch sử commit, không chạy hook, không chạy script dự án, không cài package và không build. Dữ liệu clone chỉ tồn tại trong môi trường cách ly cho tới khi hoàn tất quét.

| Công cụ | Mục tiêu | Chế độ an toàn | Diễn giải |
|---|---|---|---|
| Semgrep với bộ quy tắc đã chốt và chạy local | Mẫu mã nguồn/cấu hình có rủi ro | Tắt telemetry; chỉ quét file, không sửa mã | Cảnh báo mẫu mã, không khẳng định khai thác được |
| OSV-Scanner | Dependency trong manifest/lockfile có khớp lỗ hổng đã biết | Chỉ quét source/manifest/lockfile; không chạy lệnh `fix`, không cài dependency | Version trong manifest có thể không đúng runtime; nêu rõ khi không có lockfile |
| Gitleaks | Chuỗi có dạng secret trong working tree | Chỉ quét working tree hiện tại, không quét lịch sử; không lưu raw value | Dấu hiệu cần chủ dự án xác minh, không chứng minh credential còn hiệu lực |

Nếu một công cụ không hỗ trợ ngôn ngữ hoặc artifact của repo, đó là **không có độ phủ**, không phải kết quả sạch. Mọi output thô được giới hạn trong môi trường phân tích. Báo cáo tổng hợp không chứa giá trị secret, file, dòng, commit, hash, endpoint, package cụ thể hay mô tả có thể biến finding thành hướng dẫn khai thác.

### 7.4.1. Cấu hình bảo thủ đã chốt

Cấu hình được khóa trước pilot và dùng giống nhau cho mọi repository. Mục đích là đo các tín hiệu từ cùng một phạm vi, không phải tối đa hóa số cảnh báo.

| Thành phần | Cấu hình đã chốt | Dữ liệu giữ lại |
|---|---|---|
| Semgrep | Dùng bộ quy tắc bảo mật công khai được tải trước, ghim phiên bản và chạy local; tắt telemetry; không nhận cấu hình nằm trong repo đích | Phiên bản tool, hash bộ rule, số finding theo họ và trạng thái xác minh |
| Phạm vi Semgrep | Loại trừ thư mục build, dependency đã vendor, `node_modules`, file nén/minified và fixture test; mọi loại trừ được ghi lại | Danh sách loại trừ theo loại, không lưu đường dẫn repo |
| OSV-Scanner | Chỉ đọc manifest/lockfile và đối chiếu dependency đã khai báo; không chạy `fix`, không cài package, không build; ghi ngày snapshot cơ sở dữ liệu | Hệ sinh thái, họ finding, trạng thái lockfile/manifest và ngày snapshot |
| Gitleaks | Chỉ quét working tree tại commit hiện tại, không quét lịch sử Git; chặn lưu giá trị chuỗi có thể là secret | Số finding theo rule/họ và trạng thái xác minh; không lưu giá trị, file, dòng hay commit |
| Xác minh | Xem lại toàn bộ tín hiệu secret và finding mức cao; lấy mẫu kiểm tra phần còn lại theo rubric cố định | Nhãn Giữ lại, Báo sai/không áp dụng, Không đủ căn cứ hoặc Ngoài phạm vi |

Các bản clone được tạo nông, không chạy hook, không chạy script dự án và không tải dependency. Phiên bản chính xác của ba công cụ, hash bộ rule Semgrep, danh sách loại trừ và ngày snapshot OSV được ghi ở phụ lục trước pilot; thay đổi sau pilot chỉ được phép khi cả nhóm ghi rõ lý do và chạy lại các mẫu đã quét.

### 7.5. Chuẩn hóa, khử trùng lặp và xác minh

Kết quả được chuẩn hóa thành bản ghi tối thiểu: mã P, công cụ, họ finding, mức độ do công cụ báo, loại artifact và trạng thái xác minh. Không giữ tác giả commit, email, URL nguồn hoặc raw output trong dữ liệu phân tích phát hành.

Khử trùng lặp theo mã P + họ finding + artifact, ưu tiên gộp các cảnh báo cùng nguyên nhân. Sau đó, người nghiên cứu xem lại ngữ cảnh tối thiểu cần thiết và gán một trong bốn nhãn:

| Nhãn | Ý nghĩa |
|---|---|
| Giữ lại | Có artifact công khai phù hợp với mô tả finding, nhưng không khẳng định có thể khai thác |
| Báo sai/không áp dụng | Có bằng chứng rõ ràng cảnh báo không phù hợp với artifact quét |
| Không đủ căn cứ | Không thể xác minh mà không chạy mã, truy cập hệ thống hay thu thập thêm dữ liệu |
| Ngoài phạm vi | File sinh tự động, vendor, test fixture, ví dụ không chạy, hoặc dữ liệu không thuộc mã dự án |

Không công bố individual finding. Nếu gặp chuỗi trông như secret còn hiệu lực, dừng phân tích chi tiết, không sao chép giá trị, không thử sử dụng và không công bố; chỉ ghi nhận một biến cố an toàn trong log nội bộ tối thiểu và áp dụng quy trình báo riêng có trách nhiệm nếu cần thiết.

### 7.6. Bảo vệ dữ liệu và đạo đức

- Không dùng từ đánh giá miệt thị, không đưa giả định về việc một người cố ý phóng đại hay lừa dối.
- Không nêu tên dự án, người, tổ chức, khóa học, URL, ảnh chụp nhận diện hoặc trích dẫn cho phép nhận diện gián tiếp.
- Không lưu tên tài khoản, email, lịch sử commit hay metadata người đóng góp.
- Chỉ giữ bảng ánh xạ URL–mã P trong khu vực hạn chế, có thời hạn ngắn và xóa khi nghiên cứu hoàn tất; dữ liệu công bố chỉ là bảng tổng hợp ẩn danh.
- Không tạo tải đáng kể cho demo; mỗi luồng UI được quan sát tối đa một lần trong pilot và một lần khi thu thập chính thức, trừ khi có lỗi kỹ thuật cần xác nhận.
- Không scan hệ thống production ngoài source clone; không đăng nhập, tạo tài khoản, thu thập cookie hay dùng token.
- Công bố giới hạn phương pháp trước kết quả để tránh thay đổi tiêu chí theo finding.

## 8. Thiết kế thực nghiệm

### 8.1. Dữ liệu

| Dữ liệu | Mục đích | Đơn vị lưu/đăng |
|---|---|---|
| Nguồn quảng bá và demo công khai | Xét điều kiện đưa vào, quan sát RQ1 | Chỉ mã P và rubric tổng hợp; không phát hành URL |
| Repository công khai clone được | Quét RQ2–RQ3 | Clone tạm thời; xóa sau xử lý |
| Output thô của công cụ | Khử trùng lặp và xác minh | Không phát hành; xóa cùng bản clone hoặc sớm hơn nếu có dấu hiệu secret |
| Bảng finding chuẩn hóa | Thống kê RQ3–RQ4 | Chỉ mã P, loại finding, trạng thái xác minh và độ phủ |

Mục tiêu là 10 demo đủ điều kiện. Báo cáo luôn nêu số ban đầu, số loại trừ theo lý do, số demo quan sát được, số có source liên kết trực tiếp, số clone thành công và số repo thực sự có độ phủ từ từng công cụ. Không suy rộng thống kê ra tất cả khóa học AI hoặc toàn bộ sản phẩm AI.

### 8.2. Các cách so sánh

Đề tài không so sánh con người hay xếp hạng dự án. So sánh ba mức bằng chứng trong cùng mẫu:

| Mức | Artifact có sẵn | Có thể kết luận hợp lệ | Không thể kết luận |
|---|---|---|---|
| A. Demo quan sát được | UI, request/response do UI tạo, client asset công khai | Một số behavior và tuyên bố chức năng có/không quan sát được trong luồng thường | Chất lượng mã server, dependency, bảo mật tổng thể |
| B. Source clone được | Mã và manifest/lockfile hiện tại | Có thể quét tĩnh trong độ phủ công cụ | Sản phẩm production tương ứng hoàn toàn với mã; khả năng khai thác |
| C. Source không có/không clone được | Chỉ demo hoặc liên kết hỏng | Mức độ bằng chứng công khai bị giới hạn | Mã nội bộ có lỗi hay không; chất lượng kỹ thuật của sản phẩm |

So sánh A–C là phần cốt lõi của RQ4. Nó cho thấy một tuyên bố có thể được kiểm chứng ở tầng nào, không xác định dự án nào "tốt" hơn.

### 8.3. Chỉ số và chấm điểm

Không tạo một điểm chất lượng tổng hợp. Thay vào đó, báo cáo các chỉ số riêng với mẫu số rõ ràng:

| Nhóm | Chỉ số |
|---|---|
| Khả năng quan sát demo | Số/tỷ lệ demo có thể quan sát luồng UI đã nêu; số tuyên bố ở trạng thái quan sát được, không quan sát được, ngoài phạm vi |
| Khả năng tiếp cận source | Số/tỷ lệ demo có URL source liên kết trực tiếp; số clone nông thành công; lý do không quét được |
| Độ phủ quét | Số repo có artifact phù hợp cho từng công cụ; tỷ lệ không hỗ trợ/không có lockfile |
| Finding | Số finding thô, sau khử trùng lặp, sau xác minh; phân bố theo họ finding và trạng thái xác minh |
| Bảo vệ dữ liệu | Số output phải xóa sớm, số thao tác bị dừng do phạm vi hoặc dữ liệu nhạy cảm; không nêu dự án liên quan |

Mọi tỷ lệ kèm khoảng tin cậy 95% nếu cỡ mẫu đủ; với mẫu nhỏ, ưu tiên số đếm và khoảng Wilson hơn là kiểm định có ý nghĩa thống kê. Không suy diễn nhân quả và không diễn giải chênh lệch như tác động của AI.

### 8.4. Kiểm tra độ tin cậy

Trước nghiên cứu chính thức, chạy pilot 2 mục để kiểm tra rubric có dẫn đến thu thập quá mức hay không. Cố định rubric, cấu hình công cụ, phiên bản công cụ và tiêu chí loại trừ trước khi thu thập mẫu chính.

Nếu có người thứ hai, họ được cung cấp dữ liệu đã mã hóa và rubric, không được biết nguồn quảng bá. Hai người mã hóa độc lập tối thiểu 20% mẫu về: trạng thái source, nhãn RQ1, lý do loại trừ và trạng thái xác minh finding. Báo cáo tỷ lệ đồng thuận; trường hợp bất đồng được giải quyết bằng quy tắc viết trước, không bằng suy đoán về cá nhân.

### 8.5. Nguy cơ với độ tin cậy của kết quả

- **Thiên lệch chọn mẫu:** chỉ các demo liên kết trực tiếp từ quảng bá công khai được xét; mẫu không đại diện cho mọi khóa học AI hay mọi dự án dùng AI.
- **Demo thay đổi theo thời gian:** demo hoặc repo có thể đổi sau khi quan sát. Ghi ngày thu thập và commit nông nếu có, nhưng không công bố định danh.
- **Không có source:** đây là giới hạn kiểm chứng, không phải bằng chứng có lỗi hay không có lỗi.
- **Cảnh báo sai và độ phủ không đều:** rule/tool khác nhau theo ngôn ngữ; nêu rõ không áp dụng và không gộp thành điểm tổng quát.
- **Mã source không nhất thiết là mã đang chạy:** repo clone được không chứng minh demo triển khai từ cùng revision.
- **Không chạy ứng dụng:** thiết kế an toàn này không thể xác minh full behavior, exploitability, hiệu năng hoặc môi trường production.
- **Ẩn danh làm giảm tái kiểm tra bên ngoài:** đây là đánh đổi có chủ đích để giảm nguy cơ nhắm vào cá nhân; protocol, rubric, cấu hình và bảng tổng hợp vẫn được công bố.

### 8.6. Tái lập

Phần có thể tái lập được của nghiên cứu gồm rubric, tiêu chí chọn/loại trừ, phiên bản và cấu hình công cụ, script chuẩn hóa/khử trùng lặp, schema dữ liệu tổng hợp và bảng số liệu ẩn danh. Không phát hành clone, raw scan output, URL mapping hay dữ liệu Inspector.

Mỗi lần quét ghi phiên bản công cụ, ngày quét, hash cấu hình, mã P và trạng thái kết quả. Nếu công cụ cần tải cơ sở dữ liệu lỗ hổng, ghi ngày snapshot và không dùng lệnh sửa tự động. Semgrep dùng cấu hình local/pinned và tắt telemetry. Toàn bộ bản clone cùng output nhạy cảm được xóa theo lịch lưu giữ đã nêu.

## 9. Thử nghiệm trong môi trường an toàn

Đề tài không triển khai tại công ty Z và không tác động lên hệ thống của bên thứ ba. Môi trường là một máy cục bộ hoặc container cô lập có thư mục phân tích tạm thời, quyền mạng tối thiểu cần thiết để clone source công khai và cập nhật dữ liệu lỗ hổng. Không có secret, token cá nhân, tài khoản demo hay quyền ghi vào repository.

| Tình huống | Cách xử lý |
|---|---|
| Demo yêu cầu đăng nhập, trả phí hoặc thông tin cá nhân | Loại trừ, ghi lý do tổng hợp |
| Inspector cho thấy dữ liệu có vẻ là dữ liệu cá nhân | Không lưu nội dung, dừng quan sát phần đó |
| Repo không clone được hoặc yêu cầu xác thực | Ghi là không thể kiểm tra source; không tìm đường truy cập thay thế |
| Repo chứa hook/script có thể chạy khi thao tác | Không chạy; chỉ clone nông bằng cấu hình vô hiệu hóa hook khi cần |
| Dấu hiệu secret | Không sao chép, không thử dùng, không công bố; dừng xử lý chi tiết |
| Tool cần build/cài dependency | Không thực hiện; đánh dấu không có độ phủ |
| Finding cần kiểm tra động để xác minh | Nhãn “không đủ căn cứ”, không thử khai thác |

## 10. Đóng góp dự kiến

- **C1, đóng góp chính.** Protocol kiểm chứng có ranh giới rõ ràng giữa quan sát demo, source có thể truy cập và finding từ phân tích tĩnh.
- **C2.** Rubric ẩn danh để đánh giá mức độ evidence công khai hỗ trợ tuyên bố kỹ thuật của demo web.
- **C3.** Pipeline quét tĩnh thụ động, đa công cụ, không chạy mã đích và không lưu kết quả nhạy cảm.
- **C4.** Số liệu tổng hợp về các điểm nghẽn kiểm chứng độc lập trong mẫu; bao gồm cả "không đủ bằng chứng" như một kết quả có giá trị.

**Triết lý khoa học:** không có artifact thì không có cơ sở để tuyên bố đã kiểm tra artifact đó. Cảnh báo công cụ chỉ là giả thuyết cần bằng chứng phù hợp. Một kết quả trung thực có thể là “không biết trong phạm vi cho phép”; kết quả này tốt hơn suy diễn từ demo hoặc từ một cảnh báo thô.

## 11. Đáp ứng yêu cầu đề tài

| Yêu cầu | Nội dung trong proposal | Cần hoàn thành khi thực hiện |
|---|---|---|
| Đọc bài, từ khóa, tài liệu | Mục 5; các từ khóa gồm static analysis, SAST, dependency vulnerability, secret detection, reproducibility, auditability, AI-generated code | Khảo sát bổ sung tài liệu về artifact transparency và đánh giá mã AI |
| RQ, khảo sát hiện trạng, quy trình, thử nghiệm | Mục 6–9 | Pilot, thu thập mẫu, chạy pipeline và kiểm tra chéo |
| Đóng góp, triết lý, phương pháp đo | Mục 3, 8.3, 10 | Chốt đóng góp theo số liệu thật, không thổi phồng |
| Báo cáo thực nghiệm có thể phát triển thành bài ngắn | Mục 8, 10 và 14 | Bổ sung kết quả, giới hạn và phụ lục protocol |

Đề tài phù hợp nhất với hướng nghiên cứu/đánh giá artifact công khai, không phải đánh giá triển khai tại doanh nghiệp. Vì vậy mục tiêu thực tế là một nghiên cứu thăm dò có protocol rõ ràng, không cam kết mức đánh giá cần xác nhận từ công ty Z.

## 12. Kế hoạch

| Thời gian | Công việc | Kết quả |
|---|---|---|
| Đến 11/11 | Chốt rubric, protocol đạo đức, cấu hình công cụ; chạy pilot 2 mục | Rubric và tiêu chí loại trừ được khóa; biết pipeline có an toàn/khả thi |
| 12–17/11 | Tuyển mẫu công khai, quan sát RQ1, kiểm tra source/clone RQ2 | Bảng mã hóa ẩn danh và sơ đồ luồng mẫu |
| **18–19/11** | **Báo cáo lần 1** | Cơ sở, RQ, protocol, pilot và một phần dữ liệu RQ1–RQ2 |
| 18–24/11 | Chạy quét RQ3, chuẩn hóa, xác minh mẫu, kiểm tra chéo | Bảng finding tổng hợp và kết quả RQ3 |
| **25–26/11** | **Báo cáo lần 2** | Kết quả sơ bộ RQ1–RQ4, giới hạn, đóng góp cập nhật |
| Từ 27/11 | Phân tích RQ4, viết báo cáo và phụ lục tái lập, xóa dữ liệu định danh tạm thời | Bản báo cáo hoàn chỉnh, script/rubric và dữ liệu tổng hợp |
| 12/2026 | Hoàn thiện báo cáo tóm tắt, slide và sản phẩm nộp | Sản phẩm cuối đã kiểm tra riêng tư |

## 13. Phân công đề xuất

| # | Vai trò | Công việc | Ràng buộc |
|---|---|---|---|
| 1 | Điều phối và đạo đức | Khóa protocol, tiêu chí lấy mẫu/loại trừ, quản lý bảng ánh xạ hạn chế | Không thay đổi tiêu chí sau khi thấy kết quả |
| 2 | Tuyển mẫu | Kiểm tra nguồn quảng bá công khai, gán mã P | Không thu thập hồ sơ cá nhân hay tìm repo qua danh tính |
| 3 | Quan sát demo | Thực hiện RQ1 theo rubric | Không tương tác ngoài phạm vi UI bình thường và Inspector |
| 4 | Source availability | Kiểm tra liên kết repo, clone nông và ghi RQ2 | Không tìm đường truy cập thay thế hoặc đọc metadata người đóng góp |
| 5 | Phân tích tĩnh | Chốt cấu hình, quét, chuẩn hóa RQ3 | Không chạy mã đích hay giữ raw secret |
| 6 | Kiểm tra độc lập | Mã hóa mù 20% mẫu và review finding | Không truy cập bảng ánh xạ định danh |
| 7 | Báo cáo và tái lập | Tổng hợp RQ4, giới hạn, phụ lục và slide | Không nêu trường hợp định danh |

## 14. Sản phẩm

1. Báo cáo đầy đủ và báo cáo tóm tắt bằng tiếng Việt hoặc tiếng Anh.
2. Rubric lấy mẫu, quan sát demo, source availability và xác minh finding.
3. Script cấu hình quét, chuẩn hóa và tạo bảng tổng hợp, không chứa URL hay dữ liệu định danh.
4. Bảng số liệu tổng hợp ẩn danh, sơ đồ luồng chọn mẫu và slide báo cáo.
5. Nhật ký xóa dữ liệu tạm thời và checklist bảo vệ dữ liệu.

## 15. Rủi ro

| Rủi ro | Cách giảm |
|---|---|
| Đề tài bị hiểu là nhắm vào cá nhân | Đơn vị phân tích là artifact; ẩn danh; không dùng ngôn ngữ kết tội; chỉ nêu giới hạn evidence |
| Thu thập quá mức dữ liệu cá nhân | Tiêu chí dữ liệu tối thiểu, không đăng nhập, không lưu content/metadata định danh, xóa mapping đúng hạn |
| Demo thay đổi hoặc biến mất | Ghi ngày, trạng thái rubric và lý do; không cố truy cập bản lưu riêng tư |
| Không có nhiều repo công khai | Báo cáo đó là kết quả RQ2; không thay bằng tìm kiếm repo theo danh tính |
| Cảnh báo tool gây hiểu nhầm | Khử trùng lặp, xác minh, báo cáo theo họ finding, không nêu exploitability hay xếp hạng |
| Lộ secret trong output | Không lưu raw value, dừng phân tích, xóa output; không thử xác thực hay công khai |
| Công cụ/lockfile không hỗ trợ | Báo cáo độ phủ và “không áp dụng”, không coi là không có finding |
| Không tái kiểm tra được hoàn toàn vì ẩn danh | Công bố protocol/configuration/schema; nêu rõ đánh đổi riêng tư–minh bạch |
| Khối lượng quá lớn | Giới hạn 10 mục, pilot sớm, ưu tiên RQ1–RQ3 trước RQ4 |

## 16. Cần duyệt trước khi thực hiện

Các quyết định đã chốt trong bản nháp này:

1. Mẫu kiểm chứng sâu 10 sản phẩm demo web.
2. Chỉ công bố số liệu tổng hợp và mã P; hạn chế tối đa thông tin cá nhân.
3. Chỉ xét tuyên bố kỹ thuật có thể kiểm chứng.
4. Quan sát demo thụ động bằng UI bình thường và Inspector, không kiểm tra API chủ động.
5. Ưu tiên quét tĩnh thụ động repo GitHub/GitLab clone được; không chạy mã đích.
6. Chỉ lấy mẫu từ liên kết trực tiếp trong nguồn quảng bá công khai của khóa học AI.
7. Bảng ánh xạ URL–mã P chỉ lưu nội bộ đến hết học kỳ 2026.1, sau đó xóa.
8. Dùng cấu hình quét bảo thủ tại mục 7.4.1: Semgrep local không telemetry, OSV-Scanner chỉ manifest/lockfile, Gitleaks chỉ working tree; không quét lịch sử Git, không chạy mã đích và không lưu giá trị secret.

**Cần cả nhóm duyệt:** rubric chi tiết và phiên bản/hash cụ thể của tool trước pilot. Tên đề tài, phạm vi 10 mục, thời hạn lưu bảng ánh xạ và cấu hình quét bảo thủ đã được chốt. Chỉ sau khi duyệt các thông số cụ thể mới bắt đầu thu thập hoặc quét.

## Tài liệu tham khảo

[1] R. Idan, T. Cohen Galor, A. Shabtai, and Y. Elovici, “An empirical security analysis of open-source software used in onboard satellite systems,” arXiv:2609.15425, Sep. 2026.

[2] C. Wang, Z. Li, S. Dutta, and M. Naik, “QLCoder: A query synthesizer for static analysis of security vulnerabilities,” in *Proc. Int. Conf. Learning Representations (ICLR)*, 2026, arXiv:2511.08462.

[3] F. Fleischer và cộng sự, “Contextualizing sink knowledge for Java vulnerability discovery,” arXiv:2604.01645, 2026.

[4] M. Iranmanesh và cộng sự, “P2Patch: Exploit-guided vulnerability repair,” arXiv:2610.20245, Oct. 2026.

[5] Semgrep, “Semgrep Documentation,” tài liệu chính thức, truy cập ngày 07/11/2026. https://semgrep.dev/docs

[6] Google, “OSV-Scanner: Project Source Scanning,” tài liệu chính thức, truy cập ngày 07/11/2026. https://google.github.io/osv-scanner/

[7] Gitleaks, “Gitleaks,” repository và tài liệu chính thức, truy cập ngày 07/11/2026. https://github.com/gitleaks/gitleaks
