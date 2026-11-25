# Kết quả chạy A, B, C — wallride, aooms, autumn, dms-webapp (kien), 2026-11-25

Kịch bản: [04](../scenarios/04-chay-a-b-c-kien.md). Bảng đăng ký: [dang-ky-pr-kien.md](dang-ky-pr-kien.md). Số liệu
tính từ `triage-result.json` của 38 lượt `pr-triage run`. File thô, bảng theo PR và comment nằm trong gói nộp riêng,
không commit.

**Giữ mù cho bước gán nhãn:** hồ sơ này chỉ có số tổng của bốn repo. Không ghi nhãn B, C theo PR hay theo cảnh báo,
và không tách `likely_true` với `likely_false`.

## Cấu hình

| Mục | Giá trị |
|---|---|
| Lệnh | `pr-triage run --base <cha> --head <commit> --pr <số> --variants B,C --no-secrets --snippet-radius 40 --display C --db data/team/store.sqlite` |
| Mã | `main` @ `81929df`, prompt `v1`, Semgrep CE 1.185.0 với `p/default` (1074 luật, khớp `rulesets.lock`) |
| Mô hình | `claude-sonnet-5-5`, effort `high` |

## Số liệu tổng

| | Giá trị |
|---|---|
| Lượt `run` | 38 (wallride 14, aooms 10, autumn 7, dms-webapp 7), 38 `ok` |
| Cảnh báo của A | 173 theo từng PR (171 sau khi gộp trùng). Mỗi cảnh báo có đúng một nhãn B và một nhãn C |
| Thời gian một lượt | trung vị 41 giây, lớn nhất 186 giây, tổng 2.287 giây |
| Độ trễ một lần gọi LLM | trung vị 8,3 giây, lớn nhất 14,3 giây |
| Token B và C | 801.323 vào, 306.959 ra |

| Nhãn | B | C |
|---|---|---|
| Có kết luận (`likely_true` hoặc `likely_false`) | 132 | 130 |
| `unknown` | 41 | 43 |
| **Tổng** | **173** | **173** |
