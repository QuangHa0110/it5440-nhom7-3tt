# P08. Quét secret tích hợp

- **Status:** queued
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0013
- **Nhánh:** `trinq/secrets/scanner`
- **Bắt đầu / Kết thúc:** — / —

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
