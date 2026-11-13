# P09. Cấu hình theo repo, bộ lọc đường dẫn, ngưỡng mức độ, giới hạn

- **Status:** done
- **Người làm:** trinq (với Claude Code)
- **Quyết định cho phép:** ADR 0012 D5
- **Nhánh:** `trinq/config/repo-config`
- **Bắt đầu / Kết thúc:** 2026-11-13 / 2026-11-13

---

## Bối cảnh

Mỗi khách hàng cần chỉnh bot: bỏ thư mục test, chỉ hiện từ mức nào, giới hạn số cảnh báo. Cấu hình đọc từ nhánh đích.

## Ngoài phạm vi

Không có giao diện web để chỉnh cấu hình.

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `.pr-triage.yml` với kiểm tra schema, từ chối khóa lạ, giá trị mặc định an toàn | Test: khóa lạ và giá trị sai bị từ chối kèm thông báo rõ | — |
| T2 | Lọc cảnh báo theo `paths.exclude/include` | Test với glob `**` | T1 |
| T3 | `DisplayPolicy` có `min_severity` và `max_findings`, ghi chú phần bị cắt vào comment | Test: vượt giới hạn thì có ghi chú | T1 |
| T4 | Phân tích `CODEOWNERS` (người cuối cùng khớp thắng) | Test trên mẫu có `**`, thư mục, phủ định không hỗ trợ thì bỏ qua | — |

## Cổng

```bash
make check
```

---

## Kết quả

*Điền khi đóng.*

- **Kết quả:** `RepoConfig` (`.pr-triage.yml`) kiểm tra chặt, báo mọi lỗi cùng lúc, mặc định an toàn. `pathglob` kiểu gitignore, `codeowners` (khớp cuối thắng). `DisplayPolicy` có `min_severity` và `max_findings` sắp theo mức độ, phần bị ẩn ghi chú trong comment (không bao giờ nói là an toàn). `PrPipeline` có `finding_filter`. 187 test qua.
- **Khác kế hoạch:** thêm `severity_rank` vào `core`; ghi chú "ẩn:" nằm trong `run.notes` nhưng không tính là lỗi.
