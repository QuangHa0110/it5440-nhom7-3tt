# P08. Quét secret tích hợp

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0013
- **Nhánh:** `trinq/secrets/scanner`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Mã do bên thứ ba gửi về thường lộ secret. Bộ quét dùng chung mẫu với bộ che secret.

## Ngoài phạm vi

Không dùng gitleaks hay trufflehog. Không quét lịch sử commit.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | Chuyển mẫu secret sang `core/secrets.py`, `llm/redact` dùng lại | Test cũ của redact vẫn qua | — |
| T2 | `SecretScanner` hiện thực `ScannerPort`, che giá trị ngay khi phát hiện, bỏ qua nhị phân và tệp lớn | Test: không có giá trị nguyên bản trong cảnh báo; giá trị giữ chỗ vẫn được báo để LLM xét | T1 |
| T3 | Nối vào `build_pipeline` và cờ CLI | Chạy `run` trên repo mẫu có secret ra một cảnh báo CWE-798 | T2 |

## Cổng

```bash
make check
```

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `SecretScanner` (7 loại mẫu, bỏ qua tham chiếu biến môi trường, nhị phân, tệp lớn, thư mục phụ thuộc), mẫu dùng chung ở `core/secrets.py`. Giá trị secret bị che ở cảnh báo, đoạn mã lưu trong kho và ngữ cảnh gửi LLM. Nối vào `build_pipeline` (cờ `--no-secrets`). 148 test qua.
- **Khác kế hoạch:** thêm che secret ở `make_bundle` và `to_findings` để ADR 0013 D3 đúng cả với kho dữ liệu.
