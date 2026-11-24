<!--
Bản khảo sát tài liệu cho đề tài 3TT, soạn ngày 07/11/2026 bằng quy trình deep research có AI hỗ trợ.
Ghi chú gốc nằm trong ghi-chu/. Mục tham khảo có "Ghi chú: …" là nguồn CHƯA xác minh đầy đủ; phải đọc bản gốc trước khi trích.
-->

> **Trạng thái:** bản khảo sát để nhóm tham khảo khi chọn ý tưởng, chưa phải phần "Tổng quan" chính thức của báo cáo.
> Số liệu lấy chủ yếu từ abstract và trang HTML của bài báo. Mọi con số phải được đối chiếu với bản gốc trước khi đưa vào báo cáo.
>
> **Đã kiểm tra lại tay (07/11/2026):**
> - Bài vệ tinh arXiv:2609.15425: 22,2% cảnh báo sai trên 360 mẫu, KTC 95% 17,6–27,6% (khớp với bản PDF).
> - GONDAR arXiv:2604.01645: 41 lỗ hổng so với 8 của Jazzer, tích hợp OSS-CRS, có zero-day (khớp với bản PDF).
> - SEVRA-BENCH arXiv:2606.13757: đúng là dựng PR bằng cách đảo ngược commit vá, nhưng **mục tiêu là đo khả năng agent bị thao túng** bằng mô tả PR (15 kiểu social engineering), không phải đo khả năng phát hiện thuần. Abstract không nêu ngôn ngữ.
> - SecPRBench arXiv:2610.33509: 265 bài từ commit gây lỗi thật trong 9 hệ thống, kể cả Firefox, V8, OpenSSL (phần lớn C/C++); phê phán benchmark dựng từ bản vá.
> - "Sifting the Noise" arXiv:2601.22952 (ISSTA 2026): OWASP Benchmark + dự án Java thật với cảnh báo CodeQL + OSS-Fuzz C/C++. Abstract **không** nhắc Vul4J.
>
> Hệ quả: chưa thấy bài nào so sánh trọn A/B/C/D trên PR Java, nhưng từng thành phần đều đã có công trình rất gần.

# Dời trọng tâm 3TT từ benchmark sang công ty Z

Câu trả lời ngắn: phần "công ty Z" không nên để sau. Nó phải là trục của đề tài, vì gần như chỉ còn ở đó khoảng trống nghiên cứu mà một nhóm 7 người làm được trong 3 tuần. Cả bốn nhánh của bản nháp đều đã có công trình rất gần. Nhánh B (công cụ + LLM lọc cảnh báo) đã được "Sifting the Noise" (ISSTA 2026) làm với CodeQL trên dự án Java thật [[1]](https://arxiv.org/abs/2601.22952), và Tencent đã báo cáo trong công nghiệp mức loại bỏ 94–98% FP [[2]](https://arxiv.org/abs/2601.18844). Nhánh C (agent đọc PR) có SEVRA-BENCH, bộ khoảng 1.000 PR dựng **đúng bằng cách đảo ngược commit vá CVE** [[3]](https://arxiv.org/abs/2606.13757). SecPRBench thì phê phán thẳng cách dựng PR từ bản vá là thiếu thực tế [[4]](https://arxiv.org/abs/2610.33509). Nhánh D (kết hợp) đã có kết quả 96,9% phát hiện khi đưa cảnh báo SAST cho LLM [[5]](https://arxiv.org/abs/2602.16741). Thêm vào đó, dữ liệu Vul4J/Project KB công khai có nguy cơ cao đã nằm trong dữ liệu huấn luyện của LLM [[6]](https://arxiv.org/abs/2403.18624), [[7]](https://arxiv.org/html/2511.08462v4). Vì vậy, đề xuất chính là một hướng lai mà báo cáo này gọi là **"cổng bảo mật PR có kiểm chứng tại công ty Z"**. Nhóm triển khai cấu hình B/D thành bot bình luận không chặn trong Jenkins của Z, cho các cấu hình còn lại chạy bóng trên cùng PR, và đo năm thứ: tỷ lệ hành động của lập trình viên, tỷ lệ FP hiệu dụng, lượng TP bị đánh rơi tại tỷ lệ nền thật của Z, chi phí trên mỗi PR, và mô hình mở chạy cục bộ so với mô hình cloud. Bộ PR tạo từ CVE đảo ngược được giữ lại nhưng thu nhỏ còn 30–50 cặp, chỉ để hiệu chuẩn có kiểm soát nhiễm bẩn. Nếu lịch sử của Z đủ dữ liệu, phần mở rộng là sinh luật Semgrep từ các commit vá bảo mật cũ của Z rồi phát lại lịch sử để đo khả năng ngăn tái phát. Hướng này vừa khả thi, vì tái dùng được pipeline Jenkins đã có, vừa nhắm vào ba khoảng trống mà các ghi chú không tìm thấy công trình nào lấp. Thứ nhất là tỷ lệ hành động riêng cho cảnh báo bảo mật đã qua LLM lọc trên PR thật. Thứ hai là so sánh mô hình mở với cloud cho việc triage SAST. Thứ ba là bằng chứng DevSecOps từ một doanh nghiệp Việt Nam. Cần nói rõ hai giới hạn. Nhiều nguồn năm 2026 vẫn là preprint. Và "không tìm thấy" là kết quả tìm kiếm, chưa phải bằng chứng là không tồn tại.

## Bảy mảng tài liệu đều đông ở benchmark công khai, trống ở mã thật và người thật

Nhìn chung cả bảy mảng mà đề bài nêu, cùng một quy luật lặp lại. Giai đoạn 2023–2026 đã sản xuất rất nhiều kỹ thuật và benchmark trên CVE công khai, với con số đẹp. Thứ còn thiếu là bằng chứng triển khai trên mã độc quyền, gắn với hành vi của lập trình viên và chi phí vận hành. Bảng dưới gom lại những gì đã đông và những gì còn trống theo các ghi chú.

| Mảng | Đã đông (bằng chứng tiêu biểu) | Khoảng trống còn lại |
|---|---|---|
| LLM lọc cảnh báo SAST | IRIS: 55/120 lỗ hổng so với 27 của CodeQL [[8]](https://arxiv.org/abs/2405.17238). ZeroFalse: F1 0,912 trên OWASP [[9]](https://arxiv.org/abs/2510.02534). LLM4FPM loại hơn 85% FP [[10]](https://arxiv.org/abs/2411.03079). "Sifting the Noise": tỷ lệ FP giảm từ trên 92% xuống 6,3% [[1]](https://arxiv.org/abs/2601.22952). Tencent: 94–98% [[2]](https://arxiv.org/abs/2601.18844). Vendor: Semgrep, Datadog, Vulnhalla [[11]](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/), [[12]](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives), [[13]](https://www.cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack) | Lượng TP bị đánh rơi ở tỷ lệ FP nền thực tế. Mô hình mở so với cloud. Tác dụng của ngữ cảnh riêng của tổ chức. Tỷ lệ hành động của lập trình viên |
| Review bảo mật PR bằng LLM/agent | SecPRBench: recall 32,5–78,1% [[4]](https://arxiv.org/abs/2610.33509). SEVRA-BENCH [[3]](https://arxiv.org/abs/2606.13757). AFCRA-Bench [[14]](https://arxiv.org/abs/2610.05399). JITVul [[15]](https://aclanthology.org/2025.acl-long.1490/). Yu et al. [[16]](https://arxiv.org/abs/2401.16310). SecureReviewer [[17]](https://arxiv.org/abs/2510.26457). RealVuln [[18]](https://arxiv.org/abs/2604.13764). Claude Code `/security-review` và Sherlock, cả hai không công bố số đo [[19]](https://www.anthropic.com/news/automate-security-reviews-with-claude-code), [[20]](https://sourcegraph.com/blog/lessons-from-building-sherlock-automating-security-code-reviews-with-sourcegraph) | Chưa có nghiên cứu công nghiệp về review **bảo mật** trên PR thật có đo tỷ lệ hành động. Số liệu triển khai hiện chỉ có cho review chung: RovoDev 38,7% [[21]](https://arxiv.org/abs/2601.01129), Cihan et al. 73,8% [[22]](https://arxiv.org/abs/2412.18531) |
| Phát hiện secret | SecretBench có 15.084 secret thật [[23]](https://arxiv.org/abs/2303.06729). Precision: Gitleaks 46%, GitHub 75% [[24]](https://arxiv.org/abs/2307.00714). LLM đạt F1 0,9852 [[25]](https://arxiv.org/abs/2504.18784). Copilot secret scanning giảm FP tới 94% (con số tốt nhất do GitHub tự báo) [[26]](https://github.blog/engineering/platform-security/finding-leaked-passwords-with-ai-how-we-built-copilot-secret-scanning/) | SecretBench bị rò rỉ dữ liệu giữa tập huấn luyện và tập kiểm thử, nên điểm số bị thổi phồng [[27]](https://arxiv.org/abs/2601.22946). Chưa có so sánh trực tiếp các công cụ hiện hành trên dữ liệu 2025–2026 |
| SCA có phân tích reachability | Chỉ 1,2% dự án Maven bị ảnh hưởng bắc cầu thực sự dùng mã lỗi [[28]](https://arxiv.org/abs/2301.07972v1). VAScanner: 21,51% [[29]](https://arxiv.org/abs/2409.02753). VEX-Bench: precision của công cụ SCA chỉ 26–27%, agent đúng 84–89% với chi phí 0,075–1,08 USD/ca [[30]](https://arxiv.org/html/2609.08040) | VEX-Bench chỉ có 75 ca, không có JS, mỗi ca một nhãn vàng [[30]](https://arxiv.org/html/2609.08040). Công cụ reachability mã nguồn mở cho Java yếu [[29]](https://arxiv.org/abs/2409.02753). Gán nhãn khả năng khai thác tốn từ vài phút đến vài giờ mỗi ca |
| Kiểm thử hồi quy bảo mật | PoCGen: 77% với khoảng 0,02 USD [[31]](https://arxiv.org/html/2506.04962v3). VulEUT: 229/292 test xác nhận khai thác [[32]](https://arxiv.org/html/2409.16701v3). CVE-Genie: 51%, 2,77 USD/CVE [[33]](https://arxiv.org/abs/2509.01835). CyberGym khoảng 20% [[34]](https://arxiv.org/pdf/2506.02548v2). PoC-Gym: chỉ 65/116 PoC hợp lệ sau khi kiểm tra lại [[35]](https://arxiv.org/abs/2602.04165) | Chưa có bài nào đo test hồi quy bắt được tái phát thật trong một công ty. Meta ACH có 73% test được chấp nhận, nhưng là test quyền riêng tư, không phải bảo mật [[36]](https://arxiv.org/abs/2501.12862) |
| Sinh luật Semgrep/CodeQL bằng LLM | QLCoder: 53,4%, 2,90 USD/CVE [[7]](https://arxiv.org/html/2511.08462v4). KNighter: 37/61 checker đạt, FP khoảng 35% [[37]](https://arxiv.org/abs/2503.09002v3). Autogrep loại 71,15% luật vì quá đặc thù [[38]](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/). MoCQ [[39]](https://arxiv.org/html/2504.16057v3). BugStone-E2E [[40]](https://arxiv.org/abs/2609.05335). AutoChecker [[41]](https://arxiv.org/abs/2411.06796v3) | Không có báo cáo peer-review nào về luật do LLM sinh được triển khai trong CI doanh nghiệp. FP gần như chỉ được đo trên chính repo nguồn [[7]](https://arxiv.org/html/2511.08462v4) |
| Kiểm chứng bản vá | P2Patch: 41% số lần chạy tìm được exploit vượt qua bản vá [[42]](https://arxiv.org/abs/2610.20245). Vul4Py dùng oracle cặp exploit + chức năng [[43]](https://arxiv.org/abs/2608.00692). VulnRepairEval: 5/23 [[44]](https://arxiv.org/abs/2509.03331). Li & Paxson: khoảng 7% bản vá OSS chưa hoàn chỉnh [[45]](https://www.icir.org/vern/papers/patch-study.ccs17.pdf) | Chưa có số liệu tỷ lệ bản vá chưa hoàn chỉnh trong nội bộ một công ty |

Bảng cho thấy hai điều. Thứ nhất, các con số "loại 93–98% FP" gần như đều đến từ OWASP Benchmark, Juliet, hoặc tập cảnh báo được tuyển chọn với **tỷ lệ FP nền 76–92%** [[1]](https://arxiv.org/abs/2601.22952), [[2]](https://arxiv.org/abs/2601.18844). Đó là môi trường mà một bộ lọc hung hăng gần như không thể thua. Mọi nguồn đều nêu chung một kiểu thất bại: lọc mạnh tay thì nuốt luôn TP. Semgrep tự công bố rằng sau khi tinh chỉnh, mức đồng thuận chỉ là **41% với FP** trong khi đạt 96% với TP, tức họ chủ động hy sinh khả năng lọc để giữ TP [[11]](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/). Datadog mô tả cùng sự đánh đổi [[12]](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives). Vulnhalla ở chế độ strict thì gán nhầm một số TP thành FP [[13]](https://www.cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack).

Thứ hai, ngành phân tích tĩnh trong công nghiệp đã có sẵn một hệ đo mà mảng LLM-bảo mật gần như chưa dùng. Google định nghĩa **"effective false positive"** là cảnh báo mà lập trình viên không có hành động tích cực nào sau khi xem, và đặt ngưỡng dưới 10% cho các check chạy lúc code review [[46]](https://6826.csail.mit.edu/2020/papers/google-analysis-cacm.pdf). Facebook thì ghi nhận cùng một bộ phân tích, cùng mức FP, đạt **tỷ lệ sửa 0% khi chạy theo lô nhưng trên 70% khi chạy lúc diff** [[47]](https://6826.csail.mit.edu/2020/papers/facebook-infer-cacm.pdf). Ngay cả khi tính cả review chung, các bài triển khai LLM review gần đây (Atlassian, Beko/Qodo, ByteDance) vẫn theo truyền thống đo "tỷ lệ giải quyết" này [[21]](https://arxiv.org/abs/2601.01129), [[22]](https://arxiv.org/abs/2412.18531), [[48]](https://arxiv.org/abs/2501.15134). Nhưng không có bài nào làm cho cảnh báo bảo mật. Bài công nghiệp duy nhất về triage FP bằng LLM là của Tencent, và đó là nghiên cứu offline, trên các loại lỗi C/C++ (NPD/OOB/DBZ), không phải taint bảo mật Java [[2]](https://arxiv.org/abs/2601.18844).

Còn hai bẫy phương pháp mà mọi hướng đều phải tính đến. Trên dữ liệu thực tế đã khử trùng lặp, phát hiện lỗ hổng mức hàm bằng LLM gần với ngẫu nhiên. Trong PrimeVul, F1 của StarCoder2 giảm từ 68,26% trên BigVul xuống 3,09% [[6]](https://arxiv.org/abs/2403.18624). Nhãn trong các bộ dữ liệu lỗ hổng phổ biến sai 20–71% [[49]](https://arxiv.org/abs/2301.05456). Dấu hiệu ghi nhớ cũng xuất hiện ngay trong bài gốc của học phần: tỷ lệ thành công của QLCoder giảm từ 57,7% trên CVE trước 2025 xuống 46,2% trên CVE năm 2025 [[7]](https://arxiv.org/html/2511.08462v4).

Về bốn bài gốc: QLCoder cung cấp oracle "bắn trên bản lỗi, im lặng trên bản đã vá" [[7]](https://arxiv.org/html/2511.08462v4). P2Patch cung cấp nguyên tắc tách oracle, tức bằng chứng dùng để dựng bản vá phải khác bằng chứng dùng để đánh giá [[42]](https://arxiv.org/abs/2610.20245). Cả hai được dùng trực tiếp trong thiết kế đề xuất. Với arXiv:2609.15425, ghi chú chỉ dẫn lại hai chi tiết mà chưa kiểm chứng: tỷ lệ FP khoảng 22,2% và cách khử trùng lặp cảnh báo bằng fingerprint [[50]](https://arxiv.org/abs/2609.15425). Với GONDAR (arXiv:2604.01645), các ghi chú không phân tích gì, nên báo cáo này không đưa ra nhận định về nội dung của nó [[51]](https://arxiv.org/abs/2604.01645). Nhóm nên tự đọc hai bài này trước khi viết phần liên hệ.

## Bản nháp A/B/C/D đặt mình đúng giữa SEVRA-BENCH, Sifting the Noise và SecPRBench

Bản nháp so sánh bốn cách A–D trên PR Java dựng từ commit vá CVE của Vul4J/Project KB và tích hợp Jenkins. Thiết kế này hợp lý về kỹ thuật nhưng nằm trong vùng **đông vừa đến đông**. Ghi chú không tìm thấy bài nào chạy đủ bốn nhánh trên cùng bộ PR Java đảo ngược CVE. Tuy vậy, từng nhánh đều đã có công trình sát, nên một phản biện sẽ hỏi ngay: "Bài này khác SEVRA-BENCH, Sifting the Noise và SecPRBench ở đâu, và làm sao loại trừ việc mô hình đã thuộc lòng các CVE công khai của Vul4J?" Bảng sau đối chiếu từng nhánh.

| Nhánh trong bản nháp | Công trình gần nhất | Mức trùng |
|---|---|---|
| A: chỉ công cụ, so với C | Yu et al. thấy LLM vượt SAST khi review bảo mật trên OpenStack/Qt [[16]](https://arxiv.org/abs/2401.16310). RealVuln trên Python: điểm F3 của Claude Sonnet 4.6 là 51,7 so với 17,7 của Semgrep [[18]](https://arxiv.org/abs/2604.13764). Snyk VulnBench JS [[52]](https://arxiv.org/pdf/2606.15762) | Cao |
| B: công cụ + LLM lọc | "Sifting the Noise" dùng cảnh báo CodeQL trên dự án Java thật, nhận diện tới 93,3% FP [[1]](https://arxiv.org/abs/2601.22952). ZeroFalse [[9]](https://arxiv.org/abs/2510.02534). IRIS [[8]](https://arxiv.org/abs/2405.17238) | Rất cao |
| C: agent đọc PR từ CVE đảo ngược | SEVRA-BENCH đảo ngược commit vá trong top 10 CWE [[3]](https://arxiv.org/abs/2606.13757). AFCRA-Bench dùng đúng quy tắc PoV của Vul4J [[14]](https://arxiv.org/abs/2610.05399). SecPRBench dùng commit gây lỗi thật và phê phán PR dựng từ bản vá [[4]](https://arxiv.org/abs/2610.33509) | Rất cao |
| D: kết hợp | Thornton: đối chiếu với SAST đạt 96,9% phát hiện và cứu lại 47% số ca bỏ sót [[5]](https://arxiv.org/abs/2602.16741). Sherlock của Sourcegraph đã chạy trong sản xuất nhưng không công bố số đo [[20]](https://sourcegraph.com/blog/lessons-from-building-sherlock-automating-security-code-reviews-with-sourcegraph) | Cao |
| Cả bốn trên Vul4J/Project KB | Không tìm thấy trong một bài duy nhất | Kết hợp mới nhưng mang tính gia tăng |

Một chi tiết cần kiểm tra ngay: một snippet tìm kiếm nói tập Java thật của "Sifting the Noise" gồm 50 ca Vul4J, nhưng trang abstract không nói vậy. Ghi chú đánh dấu điểm này là **chưa xác minh** [[1]](https://arxiv.org/abs/2601.22952). Nếu đúng, nhánh B của bản nháp gần như là bản lặp lại.

Bộ dữ liệu cũng mang rủi ro riêng. Vul4J chỉ có **79 lỗ hổng tái lập được**, và nhóm duy trì cảnh báo nhiều mục, nhất là dự án Spring, không còn build được. Các bài sau thường chỉ dùng tập con 64 ca build được [[53]](https://github.com/tuhh-softsec/vul4j). Agent có thể sửa hoặc xoá test PoV của Vul4J để lái oracle [[54]](https://arxiv.org/html/2610.10150v1). PR dựng từ bản vá đảo ngược thường là diff nhỏ, tập trung. Thực tế khác hẳn: lỗ hổng thường nằm lẫn trong một PR tính năng lớn [[4]](https://arxiv.org/abs/2610.33509). Ý "diff nhỏ nên dễ hơn" là suy luận trong ghi chú, chưa phải khẳng định của SecPRBench.

Từ đó, bản nháp cần sáu chỉnh sửa, xếp theo mức độ quan trọng giảm dần trong bảng dưới.

| # | Chỉnh sửa | Cách làm cụ thể | Căn cứ |
|---|---|---|---|
| 1 | **Đưa công ty Z lên làm phần chính** | Bộ CVE đảo ngược lùi xuống thành "giai đoạn 0: hiệu chuẩn công cụ trước triển khai" | Ghi chú kết luận rằng nếu thiếu dữ liệu riêng của công ty hoặc CVE sau mốc cắt, bài sẽ bị đọc như một bản lặp lại |
| 2 | **Thu nhỏ bộ hiệu chuẩn và kiểm soát nhiễm bẩn** | Còn 30–50 ca, mỗi ca chấm theo cặp (bản lỗi bị gắn cờ, bản đã vá im lặng). Viết lại tiêu đề và mô tả PR cho trung tính, xoá mã CVE và phần diff của test. Thêm CVE năm 2026 sau mốc cắt. Chạy "identity probe" ("đây là CVE nào?") | Tiêu chí của QLCoder [[7]](https://arxiv.org/html/2511.08462v4). Probe chỉ-tên-tệp của "Sifting the Noise" [[1]](https://arxiv.org/abs/2601.22952) |
| 3 | **Báo cáo chỉ số theo từng lớp** | Precision/recall riêng cho TP và FP, tỷ lệ TP bị bộ lọc đánh rơi, FNR tại một mức FPR thấp cố định (kiểu VD-S). Không chỉ báo cáo "mức đồng thuận" gộp | VD-S của PrimeVul [[6]](https://arxiv.org/abs/2403.18624). Mức đồng thuận gộp bị lớp TP chi phối [[11]](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/) |
| 4 | **Định nghĩa các nhánh cho chặt** để D không tầm thường | B trả về TP/FP/"cần thêm dữ liệu" cho từng cảnh báo. C chỉ nhận diff và ngữ cảnh repo. D nhận cảnh báo SAST làm gợi ý nhưng được phép nêu phát hiện mới | Vulnhalla [[13]](https://www.cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack). Thornton [[5]](https://arxiv.org/abs/2602.16741) |
| 5 | **Cô lập oracle** | Agent không có quyền ghi vào test PoV. Bằng chứng để dựng và bằng chứng để đánh giá phải tách nhau | [[54]](https://arxiv.org/html/2610.10150v1), [[42]](https://arxiv.org/abs/2610.20245) |
| 6 | **Ghi chi phí và độ trễ cho từng PR ngay từ đầu** | Log token, USD, giây trên mỗi PR và mỗi cảnh báo | Ghi chú không tìm thấy số liệu chi phí/độ trễ theo PR từ một lần triển khai CI thật. Đây là phần đóng góp rẻ nhất có thể thêm |

## Năm hướng ứng viên: dễ làm và mới hiếm khi đi cùng nhau

Năm hướng dưới đây đến từ các phần "khoảng trống" của bốn ghi chú, cộng với bản nháp hiện tại. Các mức đánh giá trong bảng là phán đoán của báo cáo, dựa trên chi phí và rủi ro mà các nguồn nêu.

| Tiêu chí | H1. Triage SAST + LLM trên PR của Z (B/D thành bot) | H2. Sự cố đã vá → luật Semgrep/CodeQL + phát lại lịch sử | H3. Phễu phát hiện secret tại Z | H4. SCA + reachability + LLM xuất VEX | H5. Bản nháp A/B/C/D trên CVE đảo ngược |
|---|---|---|---|---|---|
| Khả thi trong 3 tuần | Cao: tái dùng Jenkins, khoảng 100–300 PR là thực tế | Trung bình: khoảng 1 giờ và 2,90 USD mỗi sự cố theo mức của QLCoder [[7]](https://arxiv.org/html/2511.08462v4), cần 20–60 commit vá | Rất cao: gán nhãn mỗi ứng viên chỉ mất vài giây | Thấp–trung bình: VEX-Bench cần 5 chuyên gia cho 75 ca [[30]](https://arxiv.org/html/2609.08040) | Rất cao: không phụ thuộc Z |
| Mức mới so với tài liệu | Khá: lần đầu có tỷ lệ hành động riêng cho bảo mật, so sánh mô hình mở với cloud, bối cảnh Việt Nam | Cao nhất: chưa có báo cáo trên mã độc quyền hay tỷ lệ tái phát nội bộ [[37]](https://arxiv.org/abs/2503.09002v3), [[38]](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/) | Trung bình: chủ yếu kiểm chứng lại SecretBench trên dữ liệu mới [[27]](https://arxiv.org/abs/2601.22946) | Khá: lần đầu có dữ liệu công ty, có JS, nhãn do lập trình viên xác nhận [[30]](https://arxiv.org/html/2609.08040) | Thấp: trùng SEVRA, Sifting, SecPRBench |
| Phụ thuộc quyền truy cập/dữ liệu của Z | Cao: repo, PR, lập trình viên gán nhãn | Rất cao: phải có lịch sử vá bảo mật nhận diện được | Trung bình: chỉ cần quyền đọc repo, nhưng dữ liệu rất nhạy cảm | Trung bình: lockfile và SBOM | Không |
| Đo được hiệu quả tại công ty | Trực tiếp: tỷ lệ hành động, FP hiệu dụng, phút triage, USD/PR | Gián tiếp: "lẽ ra đã bắt được" khi phát lại lịch sử, precision trên HEAD | Trực tiếp: precision, thời gian thu hồi secret | Trực tiếp: lượng cảnh báo giảm, nhưng recall khó đo | Không đo được tại công ty |
| Rủi ro chính | Ít PR trong 3 tuần; không được gửi mã ra cloud | Z không có đủ commit vá bảo mật; luật quá khớp mẫu | Ít phát hiện; ít yếu tố "phân tích chương trình" | Gán nhãn tốn kém; công cụ reachability yếu | Bị coi là bản lặp; nhiễm bẩn dữ liệu |

Không hướng nào đơn lẻ đạt cả ba tiêu chí: khả thi, mới, và có hiệu quả đo được tại công ty. H5 dễ nhất nhưng gần như không đóng góp gì và không đáp ứng tiêu chí điểm A. H2 mới nhất. Các ghi chú không tìm thấy công trình nào triển khai luật do LLM sinh trên mã doanh nghiệp, và không có số liệu tái phát lỗ hổng trong mã đóng [[7]](https://arxiv.org/html/2511.08462v4), [[55]](https://dl.acm.org/doi/10.1145/3728901). Nhưng H2 đặt cược hoàn toàn vào việc Z có đủ commit vá bảo mật được đánh dấu rõ. Đó là điều nhóm chỉ biết được sau khi đã vào công ty.

H4 rất hấp dẫn về khoảng trống: VEX-Bench tự nhận quy mô nhỏ, không có JS, và coi việc đi từ trạng thái nhị phân sang lời biện minh là "thách thức mở trung tâm" [[30]](https://arxiv.org/html/2609.08040). Nhưng gán nhãn khả năng khai thác tốn từ vài phút đến vài giờ mỗi ca. Công cụ reachability miễn phí thì chỉ thật sự tốt cho Go [[56]](https://google.github.io/osv-scanner/usage/scan-source), và Z chưa chắc dùng Go.

H3 an toàn nhất. Gitleaks có recall cao nhưng precision chỉ 46%, nên là bộ sinh ứng viên tự nhiên cho một tầng LLM lọc phía sau [[24]](https://arxiv.org/abs/2307.00714). Tuy vậy, so với chủ đề Chương 11 "phân tích chương trình hướng bảo mật", H3 mỏng về mặt phân tích chương trình.

H1 là điểm cân bằng. Nó dùng lại gần như toàn bộ pipeline và nhánh B/D của bản nháp. Các mẫu báo cáo công nghiệp cho thấy vài trăm cảnh báo được gán nhãn là đủ cho một bài công nghiệp: Tencent dùng 433 cảnh báo [[2]](https://arxiv.org/abs/2601.18844), Beko dùng 3 dự án và 22 người làm thực tế [[22]](https://arxiv.org/abs/2412.18531). Mã riêng của Z không thể nằm trong dữ liệu huấn luyện của mô hình, nên tự động giải quyết vấn đề nhiễm bẩn mà bản nháp đang vướng.

## Hướng đề xuất: cổng bảo mật PR có kiểm chứng tại Z, chạy bóng bốn cấu hình

Hướng chính là **H1 làm lõi, H5 thu nhỏ làm hiệu chuẩn, H2 làm phần mở rộng có điều kiện**, và tuỳ chọn thêm một mô-đun secret của H3 để chắc chắn có đủ phát hiện. Ý tưởng then chốt về thiết kế: trên PR thật của Z, chỉ một cấu hình (D, hoặc B nếu chi phí quá cao) được đăng bình luận công khai. A, B và C chạy bóng trên **cùng các PR đó** và lưu kết quả lại. Nhờ vậy nhóm có một so sánh ghép cặp A/B/C/D trên mã thật, không bị nhiễm bẩn, mà lập trình viên không phải đọc bốn luồng bình luận. Câu hỏi của bản nháp được giữ nguyên, chỉ chuyển sang nền dữ liệu đáng tin hơn.

### Triết lý khoa học: giá trị do lập trình viên quyết định, giả thuyết phải bác bỏ được

Đề tài nên tự định vị là một **nghiên cứu tình huống đơn, có lồng các đơn vị phân tích** (đơn vị là PR và cảnh báo), theo lập trường thực dụng. Thước đo giá trị là hành vi trong quy trình làm việc thật, không phải độ chính xác so với nhãn do tác giả tự đặt. Google viết rằng chính "developers, not tool authors" mới quyết định giá trị của một công cụ [[46]](https://6826.csail.mit.edu/2020/papers/google-analysis-cacm.pdf). Facebook chứng minh rằng cùng một bộ phân tích có tác động khác hẳn tuỳ thời điểm nó xuất hiện trong quy trình [[47]](https://6826.csail.mit.edu/2020/papers/facebook-infer-cacm.pdf).

Nghiên cứu tình huống không nhằm khái quát hoá cho cả một tổng thể. Theo chuẩn thực nghiệm ACM SIGSOFT, mục đích là "study one thing deeply", và việc không công bố dữ liệu mật không phải là một lời phê bình hợp lệ [[57]](https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md). Bù lại, mỗi giả thuyết phải phát biểu được dưới dạng có thể bác bỏ. Bằng chứng phải được đối chiếu chéo giữa ba nguồn: log CI, nhãn thủ công và khảo sát. Oracle phải được tách: tập dùng để tinh chỉnh prompt hay luật không được trùng với tập dùng để đánh giá [[42]](https://arxiv.org/abs/2610.20245), [[35]](https://arxiv.org/abs/2602.04165). Công bố trước giao thức nghiên cứu và gán nhãn theo nhóm có đo độ đồng thuận giữa người chấm là hai thuộc tính "xuất sắc" trong chuẩn này [[57]](https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md). Cả hai rẻ, nên nhóm nên làm: đóng dấu thời gian cho giao thức và giả thuyết trong repo ngay tuần 1. Chuẩn này cũng liệt kê việc dùng LLM để phân tích dữ liệu là một anti-pattern. Ghi chú lưu ý cần kiểm tra lại câu chữ chính xác [[57]](https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md), nhưng dù sao thì không nên dùng LLM để mã hoá câu trả lời khảo sát.

### Bốn câu hỏi nghiên cứu chính và một câu mở rộng

| RQ | Câu hỏi | Giả thuyết có thể bác bỏ | Dữ liệu |
|---|---|---|---|
| RQ1: Lọc ở tỷ lệ nền thật | Trên cảnh báo SAST từ mã của Z, B và D giảm bao nhiêu cảnh báo cần review, và đánh rơi bao nhiêu TP, so với A? | Ở tỷ lệ FP nền của Z, số FP tiết kiệm được trên mỗi TP bị đánh rơi thấp hơn ít nhất một bậc so với cùng cấu hình chạy trên OWASP | 200–400 cảnh báo đã gán nhãn: phát lại trên PR cũ, PR mới và HEAD |
| RQ2: Mô hình và ngữ cảnh | Mô hình mở chạy cục bộ so với cloud, kết hợp với bốn mức ngữ cảnh (prompt chung → prompt theo CWE → thêm ghi chú sanitizer/framework của Z → thêm lịch sử triage), khác nhau thế nào về độ chính xác, TP bị đánh rơi, USD và giây trên mỗi cảnh báo? | Ngữ cảnh riêng của Z thu hẹp khoảng cách giữa mô hình mở và cloud xuống dưới một ngưỡng đặt trước | Cùng tập nhãn với RQ1, chạy offline |
| RQ3: Hành vi lập trình viên | Phát hiện xuất hiện lúc PR có tỷ lệ hành động cao hơn báo cáo theo lô hay không? Tỷ lệ FP hiệu dụng và chi phí CI là bao nhiêu? | Tỷ lệ hành động lúc PR lớn hơn tỷ lệ của báo cáo lô trên cùng loại cảnh báo (kiểm định tỷ lệ) | Log bot, phản ứng trên bình luận, commit sau bình luận, khảo sát |
| RQ4: Hiệu chuẩn có kiểm soát nhiễm bẩn | Trên 30–50 cặp CVE đảo ngược và đã vá, thứ hạng A/B/C/D có giống thứ hạng trên mã Z không? Mức chênh trước và sau mốc cắt là bao nhiêu? | Nhánh C có độ chính xác theo cặp trên CVE trước mốc cắt cao hơn sau mốc cắt (dấu hiệu ghi nhớ) | Vul4J/Project KB + CVE năm 2026, identity probe |
| RQ5 (mở rộng) | Với mỗi commit vá bảo mật của Z, agent có sinh được luật Semgrep bắn trên bản lỗi và im lặng trên bản vá không? Luật sinh từ sự cố trước thời điểm t có bắt được sự cố sau t không? | Tỷ lệ sinh luật thành công trên mã Z không vượt mức 46,2% mà QLCoder đạt trên CVE năm 2025 [[7]](https://arxiv.org/html/2511.08462v4) | 20–60 commit vá, phát lại git history |

RQ1 nhắm vào một khoảng trống mà ghi chú gọi là "hầu như chưa được nghiên cứu": ảnh hưởng của tỷ lệ nền. Một phép tính minh hoạ (của báo cáo này, không lấy từ nguồn nào) cho thấy vì sao. Giả sử một bộ lọc loại 95% FP và đánh rơi 5% TP. Trên 100 cảnh báo kiểu OWASP gồm 90 FP và 10 TP, nó tiết kiệm 85,5 lần review và chỉ mất 0,5 TP, tức khoảng 171 lần review tiết kiệm cho mỗi TP mất. Trên 100 cảnh báo với tỷ lệ FP khoảng 22%, con số ghi chú dẫn lại từ bài gốc arXiv:2609.15425 và chưa kiểm chứng [[50]](https://arxiv.org/abs/2609.15425), nó chỉ tiết kiệm 20,9 lần review và mất 3,9 TP, tức khoảng 5,4 lần review cho mỗi TP mất. **Cùng một bộ lọc, giá trị ròng có thể chênh hơn 30 lần chỉ vì tỷ lệ nền.** Với ước tính 10–20 phút triage thủ công cho mỗi cảnh báo [[2]](https://arxiv.org/abs/2601.18844), đánh đổi này quy được ra giờ công cụ thể.

RQ2 nhắm vào khoảng trống thứ hai: ghi chú không tìm thấy nghiên cứu nào so sánh trực tiếp mô hình mở với GPT/Claude trong việc triage SAST tại chỗ. Bằng chứng gần nhất cho thấy khoảng cách đáng kể. Thornton đo được mô hình thương mại phát hiện 89–96%, mô hình mở 53–72% [[5]](https://arxiv.org/abs/2602.16741). "Sifting the Noise" thấy backbone yếu hưởng lợi ít từ agent [[1]](https://arxiv.org/abs/2601.22952). Trong khi đó, VEX-Bench cho thấy các mô hình loại DeepSeek-V4-Pro chỉ tốn khoảng 0,075 USD/ca mà vẫn đạt 84% [[30]](https://arxiv.org/html/2609.08040). Ràng buộc "không được gửi mã ra ngoài" của doanh nghiệp vì thế trở thành một biến nghiên cứu, thay vì chỉ là một trở ngại. Phần ablation ngữ cảnh phỏng theo cách Semgrep tăng tỷ lệ triage tự động từ khoảng 20% lên 60% nhờ "memories" [[58]](https://semgrep.dev/blog/2025/semgrep-is-confidently-handling-60-of-all-triage-for-users-without-reducing-coverage) và cách Datadog dùng ngữ cảnh sanitizer tuỳ chỉnh [[12]](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives). Ghi chú không thấy nghiên cứu học thuật nào đo tác dụng này trên mã công ty thật.

### Đóng góp: bốn điểm có thể bảo vệ trước phản biện

Đóng góp thứ nhất là bằng chứng công nghiệp đầu tiên, theo hiểu biết của nhóm, về **tỷ lệ hành động và tỷ lệ FP hiệu dụng của cảnh báo bảo mật đã qua LLM lọc, xuất hiện lúc PR**, đo trong một doanh nghiệp vừa và nhỏ tại Việt Nam. Ghi chú không tìm thấy nghiên cứu peer-review nào về DevSecOps hay SAST ở Việt Nam. Cần nói rõ rằng chưa tra các hội nghị SoICT, KSE, RIVF, nên câu chữ phải là "theo hiểu biết của chúng tôi".

Đóng góp thứ hai là một phân tích có tính đến tỷ lệ nền: lượng TP bị đánh rơi và giá trị ròng tính theo giờ công.

Đóng góp thứ ba là so sánh mô hình mở cục bộ với cloud, cùng ablation ngữ cảnh tổ chức, trên mã riêng không thể bị nhiễm bẩn.

Đóng góp thứ tư là một giao thức hiệu chuẩn A/B/C/D trên CVE đảo ngược, có cặp đối chứng và kiểm soát nhiễm bẩn. Giao thức này trả lời trực tiếp lời phê bình của SecPRBench [[4]](https://arxiv.org/abs/2610.33509). Nếu đạt phần mở rộng, có thêm con số đầu tiên về tỷ lệ tái phát lỗ hổng trong mã đóng, cùng tỷ lệ sinh luật thành công trên sự cố nội bộ [[55]](https://dl.acm.org/doi/10.1145/3728901), [[37]](https://arxiv.org/abs/2503.09002v3).

Hiện vật đi kèm gồm pipeline Jenkins, prompt, mã phân tích và số liệu tổng hợp đã ẩn danh. Định dạng bài phù hợp với kiểu "experience report" của industry track, như bài của Ericsson tại ICSME 2025 dựa trên "preliminary experiments" [[59]](https://arxiv.org/abs/2507.19115v2).

### Phương pháp đo: bốn nhóm chỉ số, mỗi chỉ số có mốc so sánh từ tài liệu

| Nhóm | Chỉ số (định nghĩa vận hành) | Mốc so sánh |
|---|---|---|
| Chất lượng tín hiệu | Precision, recall theo từng lớp trên mẫu gán nhãn. Hai người chấm, tính Cohen's kappa trên tập con | IRIS có FDR khoảng 85% [[8]](https://arxiv.org/abs/2405.17238). Tencent loại 94–98% FP [[2]](https://arxiv.org/abs/2601.18844) |
| | Tỷ lệ loại FP = số FP bị lọc / tổng số FP. Tỷ lệ TP bị đánh rơi = số TP bị lọc / tổng số TP. Trong số cảnh báo bị lọc phải lấy mẫu dư để ước lượng TP bị đánh rơi | "Sifting the Noise" cảnh báo hiện tượng nuốt TP [[1]](https://arxiv.org/abs/2601.22952) |
| | Số lần review tiết kiệm trên mỗi TP bị đánh rơi, ở tỷ lệ nền của Z | Phép tính minh hoạ ở trên |
| | FNR tại một mức FPR thấp cố định (kiểu VD-S) cho bộ hiệu chuẩn | PrimeVul [[6]](https://arxiv.org/abs/2403.18624) |
| Hành động | Tỷ lệ hành động lúc PR = phần cảnh báo có dòng bị gắn cờ được sửa, hoặc cảnh báo được đóng bằng commit, trước khi merge | Facebook 70% [[47]](https://6826.csail.mit.edu/2020/papers/facebook-infer-cacm.pdf). RovoDev 38,7% [[21]](https://arxiv.org/abs/2601.01129). Cihan 73,8% [[22]](https://arxiv.org/abs/2412.18531). BitsAI-CR 26,7% (Outdated Rate, Go) [[48]](https://arxiv.org/abs/2501.15134) |
| | Tỷ lệ hành động với báo cáo lô (dump SARIF của nợ trên HEAD) | Facebook 0% [[47]](https://6826.csail.mit.edu/2020/papers/facebook-infer-cacm.pdf) |
| | Tỷ lệ FP hiệu dụng = nhãn của lập trình viên (Sửa / Không sửa nhưng hợp lệ / FP / Không hiểu) | Ngưỡng Google dưới 10% [[46]](https://6826.csail.mit.edu/2020/papers/google-analysis-cacm.pdf) |
| | Thời gian đến khi sửa (giờ) | Coverity: trung vị 96 ngày [[60]](https://dblp.org/rec/conf/issre/ImtiazMW19.html) |
| Chi phí | USD và giây trên mỗi cảnh báo và mỗi PR. Chênh lệch thời gian CI (trung vị, p90). Phút triage tự báo cáo | Tencent: 0,0011–0,12 USD và 2,1–109,5 giây mỗi cảnh báo, so với 10–20 phút thủ công [[2]](https://arxiv.org/abs/2601.18844) |
| Cảm nhận | Khảo sát Likert (mục kiểu TAM về tính hữu ích và dễ dùng) sau tuần 2, 3–5 phỏng vấn ngắn | Là lựa chọn thiết kế: ghi chú không thấy tài liệu nào dùng TAM/SUS cho việc áp dụng SAST |

Recall trên PR thật không có ground truth đầy đủ. Vì vậy nhóm dùng **giả-oracle hợp nhất**: một lỗ hổng được tính là thật nếu bất kỳ cấu hình nào trong A–D phát hiện ra và người chấm xác nhận. Cách này phỏng theo gợi ý "union-of-tools pseudo-oracle" cho secret [[24]](https://arxiv.org/abs/2307.00714). Ngoài ra, nhóm phát lại công cụ trên N PR đã merge gần đây, theo cách Charoenwet et al. phát lại trên các commit gây lỗ hổng: một công cụ đơn lẻ chạm tới hàm lỗi ở 52% số commit, kết hợp nhiều công cụ thì 78% [[61]](https://arxiv.org/abs/2407.12241). Thiết kế tổng thể được trình bày trung thực là "quan sát trước/sau cộng phát lại hồi cứu", không phải chuỗi thời gian gián đoạn, vì 3 tuần là quá ngắn [[57]](https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md).

Quy mô mẫu cần được nói thẳng. Với 300 cảnh báo đã gán nhãn, khoảng tin cậy 95% cho một tỷ lệ quanh 50% rộng khoảng ±5,7 điểm. Nhưng nếu chỉ có 80 TP, ước lượng tỷ lệ TP bị đánh rơi quanh 5% sẽ rộng khoảng ±5 điểm. Đó là lý do phải lấy mẫu dư trong nhóm cảnh báo bị lọc. Báo cáo phải ghi mẫu số ở mọi con số.

### Phạm vi tối thiểu và phạm vi mở rộng

| Hạng mục | Tối thiểu (bắt buộc để đạt A) | Mở rộng (nếu đủ dữ liệu và thời gian) |
|---|---|---|
| Triển khai tại Z | 1–3 repo đang hoạt động. Bot D (hoặc B) bình luận không chặn. A/B/C chạy bóng. Phát lại 100–200 PR đã merge. Một báo cáo lô trên HEAD | Thêm repo. Mô-đun secret (Gitleaks + TruffleHog có xác minh + LLM lọc) để tăng số phát hiện [[24]](https://arxiv.org/abs/2307.00714) |
| Gán nhãn | Ít nhất 200 cảnh báo. Ít nhất 1 lập trình viên của Z gán nhãn tập con để tính kappa | 400 cảnh báo trở lên. Hai lập trình viên của Z |
| Mô hình | 1 mô hình cloud + 1 mô hình mở cục bộ, 2 mức ngữ cảnh | 2 + 2 mô hình, đủ 4 mức ngữ cảnh, có "memory" lịch sử triage |
| Hiệu chuẩn | 30 cặp CVE đảo ngược và đã vá, văn bản PR đã trung tính hoá, identity probe | 50 cặp, thêm CVE năm 2026 sau mốc cắt |
| RQ5 | Không có | 20–60 commit vá của Z → luật Semgrep kiểm bằng `semgrep --test`, phát lại lịch sử, precision trên HEAD [[7]](https://arxiv.org/html/2511.08462v4), [[41]](https://arxiv.org/abs/2411.06796v3) |
| Kiểm chứng bản vá | Không có | Với 3–5 sự cố web/API: test PoV fail trên bản lỗi, pass trên bản vá, có bằng chứng coverage chạm dòng đã vá [[35]](https://arxiv.org/abs/2602.04165) |
| Xác nhận | Thư hoặc email ký của CTO hay trưởng nhóm kỹ thuật, xác nhận thời gian, phạm vi và các số liệu tổng hợp. Member checking với lập trình viên | Công ty duyệt bản thảo trước khi đăng arXiv |

Lý do thêm mô-đun secret ở phạm vi mở rộng là chi phí gán nhãn: chỉ vài giây mỗi ứng viên. Nó bảo hiểm cho trường hợp PR trong 3 tuần sinh quá ít cảnh báo SAST. Cũng có lý do khoa học: điểm F1 khoảng 0,98 trên SecretBench nhiều khả năng bị thổi phồng do rò rỉ dữ liệu, nên một lần đo precision trên repo mới của Z có giá trị riêng [[25]](https://arxiv.org/abs/2504.18784), [[27]](https://arxiv.org/abs/2601.22946). RQ5 được đặt sau một **cổng quyết định ở cuối tuần 1**: chỉ làm nếu Z có ít nhất 20 commit vá bảo mật nhận diện được. Lý do là luật do LLM sinh rất dễ quá khớp mẫu: Autogrep phải bỏ 71,15% số luật [[38]](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/). Thêm vào đó, 63% số lỗ hổng tái phát là clone Type-III đã bị sửa đổi nhiều [[55]](https://dl.acm.org/doi/10.1145/3728901). Nếu làm RQ5 mà không có tập biến thể giữ riêng để đánh giá, kết quả sẽ không đứng vững.

### Kế hoạch 3 tuần cho 7 người

| Tuần | Công việc chính | Mốc kết thúc tuần |
|---|---|---|
| 1 | Ký thoả thuận truy cập và bảo mật với Z, chốt rõ có được gửi mã ra cloud hay không. Kiểm kê dữ liệu: số PR mỗi tuần, số commit vá bảo mật. Dựng pipeline Jenkins ở chế độ bóng. Chạy bộ hiệu chuẩn 30–50 cặp. Phát lại trên các PR đã merge, quét HEAD để có báo cáo lô. Đóng dấu thời gian cho giao thức nghiên cứu | Cổng quyết định: có làm RQ5 không, dùng mô hình cloud hay chỉ mô hình cục bộ |
| 2 | Bật bình luận không chặn trên PR mới, gửi báo cáo lô cho lập trình viên. Gán nhãn cảnh báo. Chạy offline lưới mô hình × ngữ cảnh trên tập đã gán nhãn. Bắt đầu RQ5 nếu qua cổng | Có ít nhất 200 cảnh báo đã gán nhãn và tính được kappa |
| 3 | Chốt số liệu hành động. Khảo sát và phỏng vấn. Phân tích, tính khoảng tin cậy. Member checking, xin thư xác nhận. Viết bản arXiv | Bản thảo đã được Z duyệt và có thư xác nhận |

Về phân vai, gợi ý một người làm đầu mối với Z kiêm phụ trách đạo đức dữ liệu, hai người lo pipeline và bot, hai người lo LLM triage và lưới mô hình, một người lo bộ hiệu chuẩn và RQ5, một người lo phân tích và viết. Việc gán nhãn chia đều cho cả nhóm: 300 cảnh báo với khoảng 15 phút mỗi cảnh báo là khoảng **75 giờ công, tức khoảng 11 giờ mỗi người**, hoàn toàn vừa sức.

Về bảo mật dữ liệu, nhóm tính chỉ số ngay bên trong Z và chỉ xuất ra CSV tổng hợp. Công ty được gọi là "Z", chỉ mô tả ngành, quy mô, stack và số người trong nhóm phát triển. Ví dụ mã được diễn giải lại hoặc tổng hợp lại thay vì trích nguyên văn, và giá trị secret được che trước khi gửi cho LLM. Ghi chú nhấn mạnh rằng quy trình "thư xác nhận" này là khuyến nghị, chưa phải một chuẩn đã được văn bản hoá ở đâu cả. Móc phương pháp luận cho nó là thuộc tính member checking trong chuẩn SIGSOFT [[57]](https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md).

## Rủi ro lớn nhất là quyền truy cập, không phải kỹ thuật

Rủi ro số một là Z chậm cấp quyền, hoặc cấm gửi mã ra ngoài. Phương án dự phòng đã nằm sẵn trong thiết kế: RQ2 biến mô hình mở cục bộ thành một nhánh chính thức, còn RQ4 chạy được mà không cần Z. Nhưng nếu đến cuối tuần 1 vẫn chưa có quyền truy cập, đề tài sẽ rơi về H5 và mất cơ hội đạt điểm A. Vì vậy, việc ký thoả thuận phải làm ngay ngày đầu.

Rủi ro thứ hai là có quá ít PR hoặc quá ít cảnh báo. Phát lại hồi cứu, quét HEAD và mô-đun secret đều nhằm đảm bảo mẫu số đủ lớn. Các mẫu công nghiệp cho thấy quy mô nhỏ vẫn chấp nhận được, miễn là sự tương phản rõ và được báo cáo trung thực: Tencent dùng 433 cảnh báo, còn bằng chứng về thất bại của chế độ lô ở Facebook chỉ dựa trên "20–30 issues" [[2]](https://arxiv.org/abs/2601.18844), [[47]](https://6826.csail.mit.edu/2020/papers/facebook-infer-cacm.pdf).

Rủi ro thứ ba thuộc về độ hợp lệ: hiệu ứng mới lạ hay Hawthorne trong thời gian ngắn, thiên lệch khi chọn repo, thiên lệch khi chọn các sự cố "có commit vá sạch" cho RQ5, và việc nhãn do sinh viên gán có thể lệch so với nhãn của lập trình viên Z. Mỗi rủi ro cần một đoạn riêng trong phần các mối đe doạ với độ hợp lệ, xếp theo bốn loại construct, internal, external và reliability [[57]](https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md).

Cuối cùng là rủi ro về nguồn. Nhiều con số then chốt chỉ được đọc ở mức abstract, hoặc là preprint năm 2026. Tên các mô hình trong SecPRBench và AFCRA-Bench chưa kiểm chứng được [[4]](https://arxiv.org/abs/2610.33509), [[14]](https://arxiv.org/abs/2610.05399). Việc "Sifting the Noise" có dùng Vul4J hay không vẫn chưa rõ [[1]](https://arxiv.org/abs/2601.22952). Venue ICLR 2026 của QLCoder chưa được xác nhận trong ghi chú [[7]](https://arxiv.org/html/2511.08462v4). Trước khi nộp, nhóm phải đọc toàn văn ít nhất SEVRA-BENCH, "Sifting the Noise", SecPRBench và bài gốc arXiv:2609.15425, vì đây chính là những bài mà phản biện sẽ dùng để so sánh.

## Kết luận

Kết luận quan trọng nhất là bản chất của đề tài phải đổi. Câu hỏi của bản nháp, "cách nào trong A/B/C/D tốt nhất", đã gần như được cộng đồng trả lời trên benchmark công khai. Phần trả lời thường là: tuỳ backbone, tuỳ CWE, và luôn phải trả giá bằng TP. Câu hỏi chưa ai trả lời là: **trong một doanh nghiệp thật, với tỷ lệ nền thật, với lập trình viên thật và ràng buộc không được gửi mã ra ngoài, cách nào tạo ra hành động sửa lỗi trên mỗi đồng chi phí?** Đây cũng chính là câu hỏi mà tiêu chí điểm A đòi hỏi.

Hệ quả thực tế là pipeline Jenkins và bốn nhánh của nhóm không bị bỏ đi. Chúng được dời từ vai trò "đối tượng nghiên cứu" sang vai trò "dụng cụ đo". Bộ CVE đảo ngược lùi xuống thành một phép thử độ tin cậy của dụng cụ. Khi đó, đóng góp của nhóm nằm ở chỗ: lần đầu tiên các chỉ số kiểu Google/Facebook được áp lên cảnh báo bảo mật đã qua LLM lọc, trong bối cảnh doanh nghiệp vừa và nhỏ tại Việt Nam.

## Tài liệu tham khảo

Các mục ghi "Ghi chú: …" là những nguồn mà ghi chú nghiên cứu đánh dấu chưa xác minh đầy đủ (chỉ qua snippet, preprint chưa có venue, hoặc số liệu vendor tự báo cáo). Bốn bài gốc của học phần được đánh dấu [Bài gốc học phần].

[1] Y. Xiong and T. Zhang, "Sifting the Noise: A Comparative Study of LLM Agents in Vulnerability False Positive Filtering," arXiv:2601.22952, v3, Jul. 2026 (to appear in ISSTA 2026). [Online]. Available: https://arxiv.org/abs/2601.22952 — *Ghi chú: thông tin "50 ca Vul4J" chỉ thấy trong snippet tìm kiếm, chưa xác minh.*

[2] X. Du, J. Feng, Y. Zou, W. Xu, J. Ma, W. Zhang, S. Liu, X. Peng, and Y. Lou, "Reducing False Positives in Static Bug Detection with LLMs: An Empirical Study in Industry," in Proc. ICSE-SEIP 2026, arXiv:2601.18844. [Online]. Available: https://arxiv.org/abs/2601.18844 — *Ghi chú: venue suy ra từ DOI 10.1145/3786583.3786910 và danh sách ICSE 2026 SEIP; trang arXiv không ghi venue.*

[3] R. Melo, R. Fogliato, S. Zhou, P. Thaker, and Z. S. Wu, "SEVRA-BENCH: Social Engineering of Vulnerabilities in Review Agents," arXiv:2606.13757, Jun. 2026. [Online]. Available: https://arxiv.org/abs/2606.13757 — *Ghi chú: chưa xem được chi tiết ngôn ngữ, mô hình, có Java/Vul4J hay không.*

[4] Y. Yang, C. Yang, Z. Zhao, A. N. Hoang, Z. Zhang, W. Wang, Z. Lyu, and L. Zhang, "Can Agentic Code Review Catch Vulnerabilities Before They Are Merged?," arXiv:2610.33509, v2, Oct. 2026. [Online]. Available: https://arxiv.org/abs/2610.33509 — *Ghi chú: tên mô hình (Grok 4.6, GPT-6 sol) chưa kiểm chứng được.*

[5] S. Thornton, "Can Adversarial Code Comments Fool AI Security Reviewers…," arXiv:2602.16741, Feb. 2026. [Online]. Available: https://arxiv.org/abs/2602.16741

[6] Y. Ding et al., "Vulnerability Detection with Code Language Models: How Far Are We?," in Proc. ICSE 2025, arXiv:2403.18624. [Online]. Available: https://arxiv.org/abs/2403.18624

[7] C. Wang, Z. Li, S. Dutta, and M. Naik, "QLCoder: A Query Synthesizer for Static Analysis of Security Vulnerabilities," arXiv:2511.08462, v4, Mar. 2026. [Bài gốc học phần] [Online]. Available: https://arxiv.org/html/2511.08462v4 — *Ghi chú: venue ICLR 2026 chưa xác minh trong ghi chú; số liệu token trong bài không nhất quán.*

[8] Z. Li, S. Dutta, and M. Naik, "IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities," in Proc. ICLR 2025, arXiv:2405.17238. [Online]. Available: https://arxiv.org/abs/2405.17238 — *Ghi chú: số liệu đổi giữa các phiên bản (69/120 ở v1, 55/120 ở bản ICLR).*

[9] M. Iranmanesh et al., "ZeroFalse: Improving Precision in Static Analysis with LLMs," arXiv:2510.02534, Oct. 2025. [Online]. Available: https://arxiv.org/abs/2510.02534

[10] Chen et al., "Utilizing Precise and Complete Code Context to Guide LLM in Automatic False Positive Mitigation," arXiv:2411.03079. [Online]. Available: https://arxiv.org/abs/2411.03079 — *Ghi chú: tình trạng peer-review chưa xác minh.*

[11] Semgrep, "Building an AppSec AI that security researchers agree with 96% of the time," Semgrep Blog, 2025. [Online]. Available: https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/ — *Ghi chú: số liệu vendor tự báo cáo, chưa kiểm chứng độc lập.*

[12] C. Maring and K. Qian, "Using LLMs to filter out false positives from static code analysis," Datadog Blog. [Online]. Available: https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives — *Ghi chú: nguồn vendor.*

[13] CyberArk Labs, "Vulnhalla: Picking the true vulnerabilities from the CodeQL haystack," CyberArk Threat Research Blog, 2025. [Online]. Available: https://www.cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack — *Ghi chú: số liệu vendor tự báo cáo.*

[14] J. Gong, J. M. Zhang, G. Jahangirova, and M. Wang, "Adaptive Code Revision Attacks on AI Pull Request Reviewers," arXiv:2610.05399, Oct. 2026. [Online]. Available: https://arxiv.org/abs/2610.05399 — *Ghi chú: tên mô hình ("Sonnet 5", "GPT-5.5") chưa kiểm chứng được.*

[15] "Benchmarking LLMs and LLM-based Agents in Practical Vulnerability Detection for Code Repositories," in Proc. ACL 2025 (Long Papers). [Online]. Available: https://aclanthology.org/2025.acl-long.1490/ — *Ghi chú: số liệu lấy từ snippet tìm kiếm.*

[16] J. Yu, P. Liang et al., "An Insight into Security Code Review with LLMs: Capabilities, Obstacles, and Influential Factors," arXiv:2401.16310, v5, Dec. 2025. [Online]. Available: https://arxiv.org/abs/2401.16310 — *Ghi chú: kết luận khác nhau giữa v4 và v5; cần trích đúng phiên bản.*

[17] F. Liu, S. Liu, Y. Zhu, X. Lian, and L. Zhang, "SecureReviewer: Enhancing Large Language Models for Secure Code Review through Secure-aware Fine-tuning," in Proc. ICSE 2026, arXiv:2510.26457. [Online]. Available: https://arxiv.org/abs/2510.26457

[18] J. Pellew and F. Raza, "RealVuln: Benchmarking Rule-Based, General-Purpose LLM, and Security-Specialized Scanners on Real-World Code," arXiv:2604.13764, Apr. 2026. [Online]. Available: https://arxiv.org/abs/2604.13764

[19] Anthropic, "Automate security reviews with Claude Code," Aug. 2025. [Online]. Available: https://www.anthropic.com/news/automate-security-reviews-with-claude-code — *Ghi chú: không có số đo precision/recall.*

[20] Sourcegraph, "Lessons from building Sherlock: Automating security code reviews with Sourcegraph," Sourcegraph Blog, Apr. 2025. [Online]. Available: https://sourcegraph.com/blog/lessons-from-building-sherlock-automating-security-code-reviews-with-sourcegraph — *Ghi chú: không có đánh giá định lượng.*

[21] "RovoDev Code Reviewer: A Large-Scale Online Evaluation of LLM-based Code Review Automation at Atlassian," in Proc. ICSE-SEIP 2026, arXiv:2601.01129. [Online]. Available: https://arxiv.org/abs/2601.01129 — *Ghi chú: mốc 44,45% cho bình luận của người chỉ thấy qua snippet.*

[22] U. Cihan et al., "Automated Code Review In Practice," in Proc. ICSE-SEIP 2025, arXiv:2412.18531. [Online]. Available: https://arxiv.org/abs/2412.18531

[23] S. K. Basak, L. Neil, B. Reaves, and L. Williams, "SecretBench: A Dataset of Software Secrets," in Proc. MSR 2023, arXiv:2303.06729. [Online]. Available: https://arxiv.org/abs/2303.06729

[24] S. K. Basak, J. Cox, B. Reaves, and L. Williams, "A Comparative Study of Software Secrets Reporting by Secret Detection Tools," in Proc. ESEM 2023, arXiv:2307.00714. [Online]. Available: https://arxiv.org/abs/2307.00714

[25] Rahman, Ahmed, Wahab, Sohan, and Shahriyar, "Secret Breach Detection in Source Code with Large Language Models," in Proc. ESEM 2025, arXiv:2504.18784. [Online]. Available: https://arxiv.org/abs/2504.18784

[26] GitHub, "Finding leaked passwords with AI: How we built Copilot secret scanning," GitHub Blog, 2024. [Online]. Available: https://github.blog/engineering/platform-security/finding-leaked-passwords-with-ai-how-we-built-copilot-secret-scanning/ — *Ghi chú: con số 94% là trường hợp tốt nhất do vendor tự báo cáo.*

[27] Soltaniani and Ghafari, "From Data Leak to Secret Misses: The Impact of Data Leakage on Secret Detection Models," arXiv:2601.22946, Jan. 2026. [Online]. Available: https://arxiv.org/abs/2601.22946 — *Ghi chú: việc benchmark là SecretBench chỉ thấy qua snippet; abstract không có số liệu.*

[28] A. M. Mir, M. Keshani, and S. Proksch, "On the Effect of Transitivity and Granularity on Vulnerability Propagation in the Maven Ecosystem," in Proc. SANER 2023, arXiv:2301.07972. [Online]. Available: https://arxiv.org/abs/2301.07972v1

[29] Zhang, Fan, Chen, Cai, Xu, and Zhao, "Does the Vulnerability Threaten Our Projects? Automated Vulnerable API Detection for Third-Party Libraries," arXiv:2409.02753, Sep. 2024. [Online]. Available: https://arxiv.org/abs/2409.02753 — *Ghi chú: venue (TSE) chưa xác nhận.*

[30] Shi, Tsien, Di et al., "VEX-Bench: Benchmarking LLM Agents for Assessing Exploitability of Software Supply Chain Vulnerabilities," arXiv:2609.08040, Sep. 2026. [Online]. Available: https://arxiv.org/html/2609.08040 — *Ghi chú: preprint, chưa có venue; tên mô hình chưa kiểm chứng.*

[31] D. Simsek, A. Eghbali, and M. Pradel, "PoCGen: Generating Proof-of-Concept Exploits for Vulnerabilities in Npm Packages," arXiv:2506.04962. [Online]. Available: https://arxiv.org/html/2506.04962v3

[32] "Unit Test Generation for Vulnerability Exploitation in Java Third-Party Libraries" (VulEUT), arXiv:2409.16701. [Online]. Available: https://arxiv.org/html/2409.16701v3 — *Ghi chú: phiên bản TSE 2025 liên quan chưa xác minh venue.*

[33] S. Ullah et al., "From CVE Entries to Verifiable Exploits: An Automated Multi-Agent Framework for Reproducing CVEs," arXiv:2509.01835, Sep. 2025. [Online]. Available: https://arxiv.org/abs/2509.01835

[34] "CyberGym," arXiv:2506.02548, v2, Oct. 2025. [Online]. Available: https://arxiv.org/pdf/2506.02548v2

[35] Gezgin, Das, Kim, Huang, Stojkovic, and C. Wang, "PoC-Gym: Towards More Reliable LLM-Assisted Proof-of-Concept Exploit Generation," arXiv:2602.04165, v3, Sep. 2026. [Online]. Available: https://arxiv.org/abs/2602.04165 — *Ghi chú: con số "71,5% PoC không hợp lệ" chưa xác minh (báo cáo này không dùng).*

[36] "Mutation-Guided LLM-based Test Generation at Meta," in Proc. FSE 2025 Industry, arXiv:2501.12862. [Online]. Available: https://arxiv.org/abs/2501.12862

[37] C. Yang, Z. Zhao, Z. Xie, H. Li, and L. Zhang, "KNighter: Transforming Static Analysis with LLM-Synthesized Checkers," in Proc. SOSP 2025, arXiv:2503.09002. [Online]. Available: https://arxiv.org/abs/2503.09002v3

[38] Lambda Security, "Autogrep: Automated Generation and Filtering of Semgrep Rules from Vulnerability Patches," technical report, Feb. 2025. [Online]. Available: https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/ — *Ghi chú: không qua peer-review; tỷ lệ FP công bố không mô tả phương pháp.*

[39] "Automated Static Vulnerability Detection via a Holistic Neuro-symbolic Approach" (MoCQ), arXiv:2504.16057, 2025. [Online]. Available: https://arxiv.org/html/2504.16057v3

[40] Q. Wu, K. Eykholt, Y. Park, X. Shu, D. Kirat, D. L. Schales, and I. Molloy, "The History Is the Detector: Executing CVE Patch History, End-to-End," arXiv:2609.05335, Sep. 2026. [Online]. Available: https://arxiv.org/abs/2609.05335

[41] "Write Your Own Code Checker: An Automated Test-Driven Checker Development Approach with LLMs," in Proc. ICSE 2026, arXiv:2411.06796. [Online]. Available: https://arxiv.org/abs/2411.06796v3

[42] M. Iranmanesh et al., "P2Patch: Exploit-Guided Vulnerability Repair," arXiv:2610.20245, Oct. 2026. [Bài gốc học phần] [Online]. Available: https://arxiv.org/abs/2610.20245 — *Ghi chú: preprint, chưa có venue.*

[43] T. Bui, T. Zhang, F. Thung, Y. Xiong, P. Jiang, X. Zhou, and D. Lo, "Vul4Py: Benchmarking Automated Vulnerability Repair in Python with Paired Exploit and Functional Oracles," arXiv:2608.00692, Aug. 2026. [Online]. Available: https://arxiv.org/abs/2608.00692

[44] Wang et al., "VulnRepairEval: An Exploit-Based Evaluation Framework for Assessing Large Language Model Vulnerability Repair Capabilities," arXiv:2509.03331, Sep. 2025. [Online]. Available: https://arxiv.org/abs/2509.03331

[45] F. Li and V. Paxson, "A Large-Scale Empirical Study of Security Patches," in Proc. ACM CCS 2017. [Online]. Available: https://www.icir.org/vern/papers/patch-study.ccs17.pdf

[46] C. Sadowski, E. Aftandilian, A. Eagle, L. Miller-Cushon, and C. Jaspan, "Lessons from Building Static Analysis Tools at Google," Commun. ACM, vol. 61, no. 4, pp. 58–66, 2018. [Online]. Available: https://6826.csail.mit.edu/2020/papers/google-analysis-cacm.pdf

[47] D. Distefano, M. Fähndrich, F. Logozzo, and P. W. O'Hearn, "Scaling Static Analyses at Facebook," Commun. ACM, vol. 62, no. 8, pp. 62–70, 2019, doi: 10.1145/3338112. [Online]. Available: https://6826.csail.mit.edu/2020/papers/facebook-infer-cacm.pdf

[48] "BitsAI-CR: Automated Code Review via LLM in Practice," in Proc. FSE 2025 Industry, arXiv:2501.15134. [Online]. Available: https://arxiv.org/abs/2501.15134 — *Ghi chú: chỉ xác nhận qua snippet/tóm tắt thứ cấp.*

[49] R. Croft, M. A. Babar, and M. Kholoosi, "Data Quality for Software Vulnerability Datasets," in Proc. ICSE 2023, arXiv:2301.05456. [Online]. Available: https://arxiv.org/abs/2301.05456

[50] arXiv:2609.15425, nghiên cứu bảo mật phần mềm mã nguồn mở cho vệ tinh. [Bài gốc học phần] [Online]. Available: https://arxiv.org/abs/2609.15425 — *Ghi chú: ghi chú KHÔNG kiểm chứng bài này; các chi tiết 22,2% FP và khử trùng lặp bằng fingerprint chỉ được dẫn lại.*

[51] GONDAR, arXiv:2604.01645. [Bài gốc học phần] [Online]. Available: https://arxiv.org/abs/2604.01645 — *Ghi chú: ghi chú không phân tích bài này; chưa kiểm chứng.*

[52] "Snyk VulnBench JS 1.0: Can LLMs Find the Same Bugs Twice?," arXiv:2606.15762, 2026. [Online]. Available: https://arxiv.org/pdf/2606.15762 — *Ghi chú: chỉ thấy qua snippet tìm kiếm.*

[53] Q.-C. Bui, R. Scandariato, and N. E. Díaz Ferreyra, "Vul4J: A Dataset of Reproducible Java Vulnerabilities Geared Towards the Study of Program Repair Techniques," in Proc. MSR 2022 Data Showcase. [Online]. Available: https://github.com/tuhh-softsec/vul4j

[54] "On the Reliability of LLM-Based Vulnerability Patching Benchmarks," arXiv:2610.10150, 2026. [Online]. Available: https://arxiv.org/html/2610.10150v1 — *Ghi chú: nội dung lấy qua tóm tắt tìm kiếm.*

[55] Cao et al., "Recurring Vulnerability Detection: How Far Are We?," in Proc. ISSTA 2025, doi: 10.1145/3728901. [Online]. Available: https://dl.acm.org/doi/10.1145/3728901

[56] Google, "OSV-Scanner: Source project scanning," OSV-Scanner documentation. [Online]. Available: https://google.github.io/osv-scanner/usage/scan-source

[57] ACM SIGSOFT, "Empirical Standards: Case Study," ACM SIGSOFT Empirical Standards repository. [Online]. Available: https://raw.githubusercontent.com/acmsigsoft/EmpiricalStandards/master/docs/standards/CaseStudy.md — *Ghi chú: câu chữ về anti-pattern "dùng LLM để phân tích dữ liệu" cần đối chiếu lại.*

[58] Semgrep, "Semgrep is confidently handling 60% of all triage for users without reducing coverage," Semgrep Blog, 2025. [Online]. Available: https://semgrep.dev/blog/2025/semgrep-is-confidently-handling-60-of-all-triage-for-users-without-reducing-coverage — *Ghi chú: số liệu vendor tự báo cáo.*

[59] Ramesh et al., "Automated Code Review Using Large Language Models at Ericsson: An Experience Report," in Proc. ICSME 2025 Industry Track, arXiv:2507.19115. [Online]. Available: https://arxiv.org/abs/2507.19115v2 — *Ghi chú: chỉ xác nhận qua snippet; không trích được số liệu.*

[60] N. Imtiaz, B. Murphy, and L. Williams, "How Do Developers Act on Static Analysis Alerts? An Empirical Study of Coverity Usage," in Proc. ISSRE 2019, pp. 323–333. [Online]. Available: https://dblp.org/rec/conf/issre/ImtiazMW19.html — *Ghi chú: chỉ xác nhận qua snippet tìm kiếm.*

[61] W. Charoenwet, P. Thongtanunam, V.-T. Pham, and C. Treude, "An Empirical Study of Static Analysis Tools for Secure Code Review," in Proc. ISSTA 2024, arXiv:2407.12241. [Online]. Available: https://arxiv.org/abs/2407.12241 — *Ghi chú: chỉ xác nhận qua snippet tìm kiếm.*
