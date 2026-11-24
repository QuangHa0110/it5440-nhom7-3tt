# P05. Pipeline và CLI: hệ thống chạy được đầu cuối

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Đóng:** mốc "hệ thống chạy được" ở tin nhắn giao việc
- **Quyết định cho phép:** ADR 0004, 0007
- **Nhánh:** `trinq/pipeline/end-to-end-run`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Nối P01 đến P04 thành lượt chạy trọn vẹn: một PR vào, `triage-result.json` ra, mọi thứ lưu trong kho.

## Ngoài phạm vi

Đăng comment lên SCM thật (P06). Gán nhãn và số đo (P07).

## Hiện trạng đã kiểm chứng

Chưa chạy gì.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `PrPipeline`: quét hai bản, lấy cảnh báo mới, trích ngữ cảnh B và C, nhận định B và C, lưu, ghi kết quả | Test với bộ giả: thứ tự gọi đúng, mọi `Verdict` được lưu | P01 đến P04 |
| T2 | Chế độ suy giảm theo mục 7.4 của kiến trúc | Test cho từng dòng của bảng: quét lỗi, ngữ cảnh lỗi, LLM lỗi, JSON sai, kho lỗi | T1 |
| T3 | `DisplayPolicy` đọc `configs/eval/display-policy.yml`, thu gọn `likely_false` | Test: `unknown` và `invalid` không bao giờ bị thu gọn | T1 |
| T4 | `triage-result.json` có schema, kiểm tra ở cả hai đầu | Test: sửa một trường thì `publish` giả từ chối | T1 |
| T5 | Lệnh `pr-triage run --repo --base --head` và `replay --from --to` trên kho Git cục bộ | Chạy trên repo mẫu cho ra kết quả, chạy lại không tạo bản ghi trùng | T1 đến T4 |
| T6 | Repo thử `tests/fixtures/sample-java-repo` hoặc script tạo repo thử trong thư mục tạm | `make e2e` tạo repo, thêm một lỗ hổng, chạy `run` | T5 |
| T7 | Chạy đầu cuối trên cổng LLM thật với repo thử | `make e2e` in ra ít nhất một cảnh báo mới, nhận định B và C, tổng token và thời gian | T6, P03 |
| T8 | Chạy trên một PR thật của repo công khai có lỗ hổng (WebGoat hoặc BenchmarkJava) | Kết quả và nhận xét ghi vào devlog | T7 |

## Cổng

```bash
make check && make e2e
```

`make e2e` yêu cầu `PR_TRIAGE_LLM_API_KEY` trong môi trường và không chạy trong CI.

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì |
|---|---|---|
| Quét Semgrep chậm trên repo lớn | `run` quá vài phút | Giới hạn đường dẫn quét theo diff, ghi vào devlog |
| Thời gian mô hình lớn | Trung vị vượt 15 phút trên repo thử | Chạy B và C song song, giảm trần ngữ cảnh |

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `make e2e` chạy được đầu cuối trên cổng LLM thật: repo Java mẫu, thêm một lỗ hổng, Semgrep thật, ngữ cảnh B và C, nhận định của <mô-hình-thử-nghiệm>, 1 cảnh báo mới, nhãn A/B/C, giải thích tiếng Việt, 1257 token vào, 494 token ra, 14,8 giây. `pr-triage run` và `pr-triage replay` có test với Semgrep thật và LLM giả. Trên cây mã WebGoat (`--base none`): 1 cảnh báo (JWT KID, SQL injection nối chuỗi), B và C đều `likely_true`, 17 giây.
- **Khác kế hoạch:** thêm `--base none` (coi mọi cảnh báo là mới, dùng để quét nhánh chính). Thêm `pipeline/build.py` lắp pipeline và `.env` nạp tự động. Trên 60 commit gần nhất của WebGoat không có cảnh báo mới (toàn commit nâng phụ thuộc), nên T8 làm trên toàn cây.
- **Ghi ở:** không có devlog mới.
