# Kết quả lọc A — wallride, aooms, autumn, dms-webapp (kien), 2026-11-25

Kịch bản: [03](../scenarios/03-loc-pr-cach-a-kien.md). Bảng đăng ký: [dang-ky-pr-kien.md](dang-ky-pr-kien.md). File
thô (JSON kết quả, SQLite) không commit.

## Cấu hình

| Mục | Giá trị |
|---|---|
| Công cụ quét | Semgrep CE 1.185.0, `p/default` (1074 luật, khớp mã băm trong `configs/semgrep/rulesets.lock`) |
| Tham số | `--variants none --no-secrets`, các tham số khác mặc định |

## Bước 1. Quét HEAD của 17 ứng viên

Ứng viên là web app Java có giấy phép mở, ít nhất 150 commit và dưới 1.000 sao. Chỉ đếm cảnh báo trong file Java.

| Repo | Cảnh báo Java tại HEAD | Luật nhiều nhất |
|---|---|---|
| tagbangers/wallride | 71 | `unrestricted-request-mapping` (65) |
| xmomen/dms-webapp | 50 | `unrestricted-request-mapping` (19), `insecure-trust-manager` (6) |
| ChukiChen/Aooms | 41 | `unrestricted-request-mapping` (39) |
| ShuaiJunlan/Autumn | 41 | `unrestricted-request-mapping` (37) |
| support-project/knowledge | 27 | `unsafe-reflection` (8), `cookie-missing-httponly` (5) |
| lizibin/black-shop | 14 | `spring-csrf-disabled` (3) |
| wine-graph/winecellar-webapp | 13 | `unrestricted-request-mapping` (11) |
| myxzjie/cms | 9 | `unrestricted-request-mapping` (3) |
| abixen/abixen-platform | 8 | `spring-csrf-disabled` (3) |
| brix-cms/brix-cms | 7 | `server-dangerous-class-deserialization` (2) |
| chrisipa/cloud-portal | 7 | `ecb-cipher` (2) |
| webpagebytes/cms | 5 | `unsafe-reflection` (4) |
| yacy/searchlab | 4 | `use-of-md5` (3) |
| byronka/minum | 2 | `unencrypted-socket` (2) |
| michaelliao/itranswarp | 2 | `use-of-sha1` (2) |
| apache/sling-org-apache-sling-app-cms | 1 | `use-of-md5` (1) |
| whoiszxl/shopzz | 0 | |

## Bước 2. Tìm commit đưa cảnh báo vào bằng `git blame`

| Repo | Commit đưa cảnh báo vào | Có cha, 1–1.000 dòng thay đổi |
|---|---|---|
| wallride | 24 | 15 |
| aooms | 15 | 10 |
| dms-webapp | 19 | 10 |
| autumn | 13 | 7 |

## Bước 3. Cách A trên cặp (cha, commit)

| Repo | Cặp đã chạy | Có cảnh báo mới trong file Java | Cảnh báo mới trong file Java |
|---|---|---|---|
| wallride | 15 | 14 | 48 |
| aooms | 10 | 10 | 40 |
| autumn | 7 | 7 | 20 |
| dms-webapp | 9 | 7 | 9 |
| **Tổng** | **41** | **38** | **117** |
