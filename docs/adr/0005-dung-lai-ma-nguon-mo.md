# ADR 0005 — Dùng lại mã nguồn mở ở tầng công cụ, kế thừa ý tưởng ở tầng phương pháp, không fork bot có sẵn

- **Status:** accepted (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [architecture.md](../architecture.md) mục 4

## Bối cảnh

Khảo sát (2026-11-13) tìm thấy `sast-triage` (MIT), `sift-sast` (Apache-2.0), `Vulnhalla` (Apache-2.0), `IRIS` (MIT), `seclab-taskflows` (MIT) và `mantis` (Apache-2.0). Chưa dự án nào có đánh giá tại doanh nghiệp, và các dự án gần nhất tự nhận chưa đo độ chính xác hoặc rất ít người dùng. Giá trị của nhóm nằm ở thiết kế đo lường và so sánh B với C, không ở việc viết bot.

## Quyết định

- **D1.** Dùng trực tiếp, như thư viện hoặc tiến trình con: Semgrep CE, SpotBugs với FindSecBugs (Java), định dạng SARIF 2.1.0, tree-sitter, scipy và statsmodels.
- **D2.** Không fork `sast-triage` hay `sift-sast`. Kế thừa ý tưởng và ghi nguồn trong docstring của mô-đun tương ứng.
- **D3.** Không dùng CodeQL trên mã của Z. Điều khoản của CodeQL hạn chế dùng trong CI trên mã không phải mã nguồn mở khi không có giấy phép GitHub Advanced Security. Có thể dùng cho dữ liệu công khai ở RQ4 sau khi đọc lại điều khoản hiện hành.
- **D4.** Không dùng dịch vụ lọc cảnh báo trả phí hay gửi mã ra ngoài (Semgrep Assistant và tương tự), vì đó là thứ đề tài muốn đo độc lập.
- **D5.** Mọi mã sao chép từ dự án khác phải ghi giấy phép và nguồn ở đầu file. Mặc định không sao chép mã.

## Phương án khác

- **Fork `sast-triage` làm khung:** có sẵn Action và comment, nhưng thiết kế dựa trên agent đọc repo ngược với ADR 0003, nhóm sẽ phải gỡ nhiều hơn viết.
- **Dùng `sift-sast` làm bộ dựng ngữ cảnh:** gần nhất với cách C nhưng khớp lời gọi theo tên và không báo chỗ nhập nhằng. Là phần nhóm muốn cải tiến và đo.

## Hệ quả

- **Tốt hơn:** ít mã tự viết ở tầng công cụ, tập trung vào phần có giá trị nghiên cứu.
- **Tệ hơn:** phụ thuộc vào phiên bản công cụ ngoài. Phải ghi phiên bản vào manifest.
- **Từ nay phải đúng:** phiên bản Semgrep, SpotBugs và bộ luật được ghi trong mỗi lượt chạy. Phạm vi phân tích vết xuyên file của Semgrep CE phải được đo bằng một ca thử trước khi viết vào báo cáo.
