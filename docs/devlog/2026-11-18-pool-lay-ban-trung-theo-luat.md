# Pool lấy cả bản trùng theo luật mà pipeline đã gộp

- **Mức độ:** 🟠 major (đóng TD-3)
- **Ngày:** 2026-11-18
- **Liên quan:** kết quả 2026-11-18 mục 5, runbook mục B9

## Phát hiện

Sau B8, 22/143 mục `eval` không có nhận định B/C. Cả 22 đều cùng file, cùng CWE, cách ≤ 3 dòng với một cảnh báo khác đã được nhận định. `PrPipeline._run` ghi occurrence cho mọi cảnh báo thô ở head, nhưng chỉ nhận định (kể cả A hình thức) các cảnh báo sau `deduplicate`. `build_pool` dựng từ occurrence nên nhận cả bản bị gộp.

## Xử lý

- Phân tích `eval` loại 22 bản trùng trên bản sao DB (`eval-final.sqlite`), n = 121.
- Commit `fix(eval): pool chỉ lấy cảnh báo pipeline đã xử lý sau gộp trùng`: `build_pool` chỉ nhận cảnh báo có ít nhất một nhận định trong lượt chạy. Test `test_pool_excludes_findings_merged_away_by_dedup` (đỏ trước, xanh sau); helper test `add_run` nay luôn tạo nhận định A như pipeline thật. Toàn bộ: 272 passed, 1 skipped.
- Dựng lại pool trên bản sao `history.sqlite` bằng mã đã sửa: `dev` 84, `eval` 121, **trùng khớp** tập đã loại bằng tay. Số đo đã báo không đổi.

## Vì sao quan trọng

Pool là mẫu số của mọi số đo RQ1/RQ2. Bản trùng làm cỡ mẫu phồng và tạo mục không có nhận định. Tập `dev` không bị ảnh hưởng vì không có cảnh báo trùng giữa các luật.
