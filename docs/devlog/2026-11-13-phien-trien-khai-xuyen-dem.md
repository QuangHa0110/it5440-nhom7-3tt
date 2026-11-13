# Tóm tắt phiên triển khai P01 đến P07

- **Ngày:** 2026-11-13. Người dùng duyệt ADR 0003 đến 0011 và kế hoạch P01 đến P07 rồi giao Claude Code triển khai (quy tắc ở `docs/plans/README.md`).

## Đã xong

Cả bảy kế hoạch ở `docs/plans/done/`. Gói `src/pr_triage/`: `core`, `store`, `scan`, `normalize`, `context`, `llm`, `pipeline`, `bot`, `evaluation`, `cli`. `make check` qua với 144 test (ruff, mypy strict). Mốc "hệ thống chạy được": `make e2e` chạy trên cổng LLM thật, ra một cảnh báo mới, nhận định B và C, comment, phản hồi `fp` ra trạng thái `marked_false`.

Mỗi kế hoạch một nhánh cá nhân (`trinq/core/...`, `trinq/scan/...`, `trinq/llm/...`, `trinq/context/...`, `trinq/pipeline/...`, `trinq/bot/...`, `trinq/evaluation/...`), mỗi nhánh gộp vào `dev` cục bộ bằng fast-forward. **Chưa push gì.**

## Quyết định tự đưa ra (ngoài ADR)

- LangGraph là engine mặc định (`--engine graph`), `plain` làm mốc đối chiếu. Hai bản có test trùng kết quả.
- ADR 0006 D5 sửa trước khi chấp nhận: bí danh hóa ở `Exporter` và khi thu `FeedbackEvent`, kho lưu giá trị gốc.
- `ScannerPort.scan` trả `list[RawFinding]` thay vì SARIF thô.
- Bán kính cửa sổ cách B mặc định 10 dòng, có cờ `--snippet-radius`.
- `--base none` coi mọi cảnh báo là mới (quét cả nhánh chính).
- Luật Semgrep viết tay (`configs/semgrep/java-injection.yml`) chỉ phủ SQL injection. Danh mục ngữ cảnh (`configs/context/java.yml`) phủ thêm vài CWE nhưng chưa có luật quét tương ứng.

## Phát hiện (đã ghi devlog riêng)

- Semgrep CE không nối taint xuyên hàm và không sinh vết trong SARIF.
- Cách C trên BenchmarkJava: nguồn tìm thấy 26/30, `missing` 4/30. Kiểm tra luồng đánh giá: C đúng 27/30, B (±10 dòng) 19/30. Đây không phải kết quả của đề tài.

## Chưa làm hoặc chưa kiểm chứng

- Chưa gọi GitHub thật (`GitHubScm` chỉ test bằng máy chủ giả HTTP). Chưa cài Jenkins hay file pipeline CI cho Z.
- SpotBugs và FindSecBugs chưa tích hợp. Chưa có phân tích cho ngôn ngữ ngoài Java.
- Chưa tải trọng lớn: `SymbolIndex.calls_of` quét lại toàn repo cho mỗi truy vấn, sẽ chậm trên repo lớn.
- Chưa so sánh mô hình chạy tại chỗ với mô hình trên cổng (H2c).
- `CODEOWNERS` dùng tên tài khoản đoán từ proposal. Branch protection chưa bật (TD-1).
- Khóa API đã dán vào hội thoại: nên đổi.

## Tái chạy

```bash
make check
PR_TRIAGE_LLM_BASE_URL=http://localhost:11434/v1
PR_TRIAGE_LLM_MODEL=
```
