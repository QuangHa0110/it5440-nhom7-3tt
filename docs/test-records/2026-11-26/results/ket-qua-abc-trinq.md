# Kết quả chạy A, B, C — hmcts, openhospital (trinq), 2026-11-26

Kịch bản: [02](../scenarios/02-chay-a-b-c-trinq.md). Bảng đăng ký: [dang-ky-pr-trinq.md](dang-ky-pr-trinq.md). Số liệu tính từ `triage-result.json` của 19 lượt. File thô và comment nằm ngoài Git.

**Giữ mù cho bước gán nhãn:** chỉ ghi số tổng. Không ghi nhãn theo PR hay theo cảnh báo, không tách `likely_true` với `likely_false`.

## Cấu hình

| Mục | Giá trị |
|---|---|
| Mã | tag `v0.1.0` (`a31e678`), prompt `v1`, `manifest_hash` `abb1e066d252` cho cả 19 lượt |
| Quét | Semgrep CE, `p/default`, khớp `rulesets.lock`, `--no-secrets` |
| B, C | `--snippet-radius 40 --display C`, trần token mặc định |
| Mô hình | `openai/Qwen/Qwen3.6-35B-A3B` |

## Cách A

| | hmcts | openhospital | Tổng |
|---|---|---|---|
| PR | 13 | 6 | 19 |
| Cảnh báo mới | 31 | 13 | 44 |
| Trong file Java | 6 | 6 | 12 |
| Ngoài Java | 25 | 7 | 32 |

| CWE | hmcts | openhospital | Tổng |
|---|---|---|---|
| CWE-732 | 23 | 0 | 23 |
| CWE-352 | 6 | 0 | 6 |
| CWE-798 | 0 | 6 | 6 |
| CWE-89 | 0 | 5 | 5 |
| không ghi | 1 | 0 | 1 |
| CWE-262 | 1 | 0 | 1 |
| CWE-1357 | 0 | 1 | 1 |
| CWE-470 | 0 | 1 | 1 |

## Cách B và C

| Cảnh báo | Nhãn | B | C |
|---|---|---|---|
| Java (12) | Có kết luận | 9 | 9 |
| Java | `unknown` | 3 | 3 |
| Ngoài Java (32) | Có kết luận | 32 | 32 |
| Ngoài Java | `unknown` | 0 | 0 |

B và C cùng nhãn: 10/12 cảnh báo Java, 30/32 cảnh báo ngoài Java.

## Vận hành

| | Giá trị |
|---|---|
| Thời gian một lượt | trung vị 28 giây, lớn nhất 58 giây, tổng 657 giây |
| Độ trễ một lần gọi LLM | trung vị 9,6 giây, lớn nhất 26,5 giây |
| Token B và C | 144.844 vào, 18.042 ra |

## Giới hạn

- **Mẫu Java nhỏ (12 cảnh báo)**, không đủ để kết luận C khác B.
- **32 cảnh báo ngoài Java** (chủ yếu CWE-732 trong tệp Compose, lặp lại qua nhiều PR). C không có ngữ cảnh luồng dữ liệu cho các tệp này (ADR 0019 D6), nên không đưa vào so sánh B với C. Chênh lệch nhãn ở nhóm này đến từ dao động của mô hình hoặc khác biệt đầu vào, chưa tách được.
- **Chưa có nhãn người gán**, nên chưa có độ chính xác, tỉ lệ loại cảnh báo sai hay loại nhầm.
- **Mô hình khác đợt của kien** (#24 dùng `claude-sonnet-5-5`). Không gộp chung khi tính số đo B, C nếu nhóm chưa thống nhất mô hình.
- Một số PR cũ (2017 đến 2020); mô hình có thể đã thấy mã này khi huấn luyện.
