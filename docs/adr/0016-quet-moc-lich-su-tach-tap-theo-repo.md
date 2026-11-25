# ADR 0016 — Lấy cảnh báo bằng quét mốc lịch sử của 6 repo, tách `dev`/`eval` theo nguyên repo

- **Status:** accepted (2026-11-18). Thay một phần D1 của [ADR 0015](0015-danh-gia-ma-nguon-mo-nhan-ai.md) (nguồn cảnh báo và cách tách tập); các điểm khác của ADR 0015 giữ nguyên.
- **Người quyết định:** người phụ trách đợt đánh giá (nhánh `feature/test-logs-minh`)
- **Liên quan:** thiết kế mục 6.3a, runbook

## Bối cảnh

- Pilot replay 60 PR/commit (OpenMRS, DSpace, OFBiz, mỗi repo 20) ở chế độ chỉ quét cho **1** cảnh báo mới; nhánh chính của ba repo có tổng 70 cảnh báo (0,04–0,07 trên 1.000 dòng Java). Mức tối thiểu của pool là 200.
- Quét 21 mốc lịch sử (11/2016 → 11/2026) của 6 repo cho 227 cảnh báo duy nhất. Khoảng 72% cảnh báo của ba repo đầu đã có ở mốc 2016, nên tách theo thời gian làm `eval` quá nhỏ.

## Quyết định

- **D1.** Nguồn cảnh báo chính là hợp các cảnh báo duy nhất trên 21 mốc first-parent mỗi repo (`pr-triage run --base none --variants none`). Báo cáo gọi đây là cảnh báo trên mã nguồn, không phải cảnh báo trên PR. Replay PR chỉ dùng cho phần mô tả RQ3.
- **D2.** Sáu repo: DSpace, OpenMRS Core, Apache Roller (`eval`, 143 ca); Apache OFBiz, OpenCms, Apache JSPWiki (`dev`, 84 ca). Mỗi repo thuộc trọn một tập. Phân chia chốt trước khi gán nhãn và không đổi sau khi đã xem nhãn hay nhận định.
- **D3.** Bỏ tiêu chí mật độ ≥ 1 cảnh báo/1.000 dòng và tiêu chí ≥ 150 PR của thiết kế 6.2.
- **D4.** Cảnh báo trùng do đổi tên/di chuyển file được đánh dấu khi gán nhãn; nếu `eval` sau khi loại trùng < 140 thì báo cỡ mẫu thực tế.

## Phương án khác

- **Tách theo thời gian:** đúng proposal 7.3 nhưng `eval` chỉ còn vài chục ca.
- **Chia ngẫu nhiên từng cảnh báo:** cỡ mẫu cân, nhưng cảnh báo cùng repo (cùng phong cách mã, cùng luật) nằm ở cả hai tập, prompt chỉnh trên `dev` dễ khớp quá mức với `eval`.
- **Chấp nhận 70 cảnh báo nhánh chính:** khoảng tin cậy quá rộng.

## Hệ quả

- **Tốt hơn:** đủ mức tối thiểu 200; `eval` gồm repo hoàn toàn chưa thấy khi chỉnh, nên đánh giá khái quát giữa repo.
- **Tệ hơn:** mất khung "tại thời điểm PR" cho RQ1/RQ2; phân bố CWE giữa hai tập không giống hệt (Roller làm `eval` nhiều CWE-79, `dev` có CWE-78/90). Biên `eval` mỏng (dư 3 ca).
- **Từ nay phải đúng:** `eval pool` chạy với `--eval-only-repo DSpace --eval-only-repo openmrs-core --eval-only-repo roller` và `cutoff` xa; báo cáo nêu rõ nguồn cảnh báo và phân chia theo repo.
