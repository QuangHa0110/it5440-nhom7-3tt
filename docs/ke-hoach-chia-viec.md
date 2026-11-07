# Kế hoạch chia việc

**Kế hoạch chia việc của Nhóm 7 cho đề tài 3TT**

| | |
|---|---|
| Phiên bản | 0.1, bản nháp để cả nhóm góp ý |
| Phạm vi | RQ1–RQ3 và demo trên bản fork. Phần công ty Z đang tạm gác |
| Tài liệu liên quan | `docs/proposal-3TT.md`, `docs/quy-uoc-chung.md` |

## 1. Cách chia

Nhóm chia việc theo kết quả phải giao, không chia theo chuyên môn. Mỗi người nhận trọn một phần, dùng AI để làm và tự chịu trách nhiệm kiểm chứng kết quả.

- Mỗi phần có một người chịu trách nhiệm và một người dự phòng.
- Các phần làm việc với nhau qua định dạng trong quy ước chung.
- Con người quyết định đáp án, nhãn, cách chấm và kết luận.

## 2. Bảy phần công việc

| # | Phần giao | AI hỗ trợ | Người phụ trách phải tự kiểm tra | Xong khi | Phụ trách | Dự phòng |
|---|---|---|---|---|---|---|
| 1 | Bài có lỗi | Tìm CVE, viết script đảo commit, build thử | Lỗi có thật trong `head` và đã hết ở `base` | Có 40–60 bài | | |
| 2 | Đối chứng và tổng quan | Lấy pull request qua API, tóm tắt bài báo | Đọc bài gốc, kiểm tra trích dẫn có thật | Có bộ đối chứng và phần tổng quan | | |
| 3 | Chương trình lõi và cách A | Viết bước quét, chuẩn hóa, khử trùng lặp | Đối chiếu tay kết quả trên vài bài | Chạy trọn bộ dữ liệu | | |
| 4 | Cách B | Viết prompt, script gọi LLM | Prompt không lộ đáp án, đọc mẫu câu trả lời | Có kết quả đủ 3 lần chạy | | |
| 5 | Cách C và D | Viết vòng chạy agent, kiểm tra JSON | Môi trường cách ly, không có internet, chi phí đúng | Có kết quả đủ 3 lần chạy | | |
| 6 | Đánh giá và thống kê | Viết script tính chỉ số, vẽ bảng | Tính tay lại một phần, kiểm tra phương pháp thống kê | Có bảng kết quả tái lập được | | |
| 7 | Jenkins, comment và demo | Viết Jenkinsfile, script comment | Token an toàn, che secret, chạy thật trên fork | Có demo và video | | |

**Việc chung:**

- Trưởng nhóm là một trong bảy người, kiêm điều phối và làm việc với thầy.
- Mỗi người tự viết phần báo cáo và slide của phần mình.
- Một người rà văn phong toàn bộ ở tuần cuối.

## 3. Việc theo giai đoạn

| Phần | Đến 11/11 | 12–17/11 | 18–24/11 | Từ 27/11 |
|---|---|---|---|---|
| 1. Bài có lỗi | Chọn CVE, thử 10 bài | Hoàn thiện 40–60 bài, khóa bộ `eval` | Sửa lỗi dữ liệu nếu có, giữ đáp án khi chấm | Viết phần dữ liệu |
| 2. Đối chứng và tổng quan | Khảo sát nghiên cứu liên quan | Dựng bộ đối chứng, viết tổng quan | Chấm báo cáo, viết phần đóng góp | Hoàn thiện bản arXiv |
| 3. Lõi và cách A | Định dạng dữ liệu, chạy công cụ trên mẫu | Khử trùng lặp, xếp ưu tiên, chạy cách A | Sửa lỗi lõi, chấm báo cáo | Viết phần RQ1 |
| 4. Cách B | Chọn mô hình, thử trên mẫu | Viết prompt trên phần `dev`, kiểm tra kết quả | Chạy B trên `eval`, đo chi phí | Viết phần RQ2 |
| 5. Cách C và D | Dựng môi trường cách ly, thử agent | Chạy C trên phần `dev`, ước tính chi phí | Chạy C và D trên `eval` | Viết phần RQ3 |
| 6. Đánh giá | Khung tính chỉ số trên dữ liệu mẫu | Tiêu chí chấm, cấu hình thí nghiệm | Tổ chức chấm, thống kê, kiểm định | Bảng, biểu đồ cuối |
| 7. Jenkins và demo | Jenkins Docker, image công cụ | Jenkinsfile gọi chương trình lõi | Chọn dự án fork, thử webhook | Comment, demo, video |

## 4. Mốc chung

| Ngày | Mốc |
|---|---|
| 09/11 | Chốt định dạng dữ liệu, giao diện lệnh, cấu trúc repo, quy tắc Git và AI |
| 11/11 | Có kết quả thử 10 bài |
| 12/11 | Chốt danh sách CWE, điều kiện chọn bài |
| 15/11 | Chốt quy tắc chấm |
| 17/11 | Khóa bộ dữ liệu `eval` và cấu hình thí nghiệm, cách A chạy trọn |
| 18–19/11 | Báo cáo lần 1 |
| 24/11 | B, C, D có đủ số liệu, xong chấm và thống kê |
| 25–26/11 | Báo cáo lần 2 |
| Từ 27/11 | Demo, viết báo cáo, bản arXiv, slide |

## 5. Làm song song

Bảy phần đều bắt đầu được ngay sau khi có định dạng dữ liệu và file mẫu.

| Phần | Dùng tạm khi chưa có dữ liệu thật | Cần gì để hoàn tất |
|---|---|---|
| 1 | Không cần | Nhóm chốt CWE |
| 2 | Không cần | Danh sách dự án từ phần 1 |
| 3 | Bài mẫu | Bộ dữ liệu từ phần 1, 2 |
| 4 | Cảnh báo mẫu | Kết quả cách A |
| 5 | Bài mẫu | Bộ dữ liệu; cách D cần thêm kết quả từ phần 3 |
| 6 | Kết quả mẫu | Kết quả A–D và đáp án |
| 7 | Lệnh giả thay chương trình lõi | Chương trình lõi hoàn thiện |

Ba điểm phải đi theo thứ tự:

1. Khóa bộ dữ liệu trước khi chạy thực nghiệm cuối cùng.
2. Cách A xong trước B và D.
3. Chấm điểm và thống kê sau khi đủ kết quả.

Cả nhóm ghép thử mỗi hai ngày để phát hiện sớm lỗi khi nối các phần.

## 6. Mốc quyết định

| Mốc | Câu hỏi | Nếu không đạt |
|---|---|---|
| 11/11 | 10 bài thử có tạo và build được không? | Đổi nguồn CVE, hoặc giảm mục tiêu còn khoảng 30 bài |
| 17/11 | Cách A đã chạy trọn bộ dữ liệu chưa? | Hoãn phần phụ, tập trung cho cách A trước báo cáo lần 1 |
| 24/11 | B, C, D đã có đủ số liệu chưa? | Giảm số lần chạy lặp, hoặc bỏ bản LLM local |

Điểm dễ nghẽn nhất là phần 1 và phần 3, vì nhiều phần phải chờ dữ liệu thật và chương trình lõi.

## 7. Phân công chấm

- Thành viên phần 4 và 5 không chấm, vì đã thấy kết quả của các cách.
- Thành viên phần 1, 2, 3, 6 và 7 chấm luân phiên theo cặp.
- Người giữ đáp án chỉ mở đáp án sau khi người chấm đã đọc xong báo cáo.
- Việc chấm dự kiến mất 20–40 giờ công, và được chia đều trong tuần 18–24/11.

## 8. Cách làm việc

- Họp 20 phút vào thứ Hai và thứ Năm. Mỗi người nói đã xong gì, sắp làm gì và đang vướng gì.
- Mỗi việc là một issue trên GitHub, có người nhận và hạn.
- Mỗi người làm trên nhánh riêng, cần một người review trước khi merge.
- Khi phần của mình có nguy cơ trễ, báo ngay trong ngày cho trưởng nhóm.

## 9. Việc của ngày đầu

1. Trưởng nhóm điền tên người phụ trách và dự phòng cho từng phần.
2. Thành viên phần 3 đề xuất định dạng JSON và file mẫu để cả nhóm góp ý.
3. Thành viên phần 1 chọn 10 CVE để thử.
4. Trưởng nhóm gửi câu hỏi cho thầy về việc tạm gác công ty và quy định dùng AI.
5. Trưởng nhóm tạo `AGENTS.md` và các issue đầu tiên.
