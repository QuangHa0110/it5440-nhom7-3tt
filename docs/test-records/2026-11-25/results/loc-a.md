# Kết quả lọc A — logicaldoc và mesh, 2026-11-25

Kịch bản: [01](../scenarios/01-loc-pr-cach-a.md). Bảng đăng ký: [dang-ky-pr.md](dang-ky-pr.md). Số liệu dưới đây lấy
từ `prefilter.json` (tầng 1) và `replay-*-merged.json` (tầng 2) của `scripts/filter_prs.py`. File thô không commit.

## Cấu hình

| Mục | Giá trị |
|---|---|
| Công cụ quét | Semgrep CE 1.185.0, bộ luật `p/default` (1074 luật, khớp mã băm trong `configs/semgrep/rulesets.lock`) |
| Tham số tầng 2 | `--variants none --no-secrets`, các tham số khác mặc định như `pr-triage replay` |
| Trần thời gian quét | 1.200 giây cho mỗi lượt quét ở tầng 2 (mặc định của dự án là 300). Máy dùng chung, tải khoảng 26 trên 16 lõi, một lượt cũ với trần 300 giây bị `failed`. Trần mỗi file giữ nguyên 30 giây như pipeline |
| Máy | Máy chủ Linux dùng chung, 16 lõi. Mọi tiến trình chạy với `nice` |

## Mật độ cảnh báo mới

| | logicaldoc | mesh |
|---|---|---|
| Commit first-parent trong cửa sổ | 600 | 600 |
| Commit sửa 1–1.000 dòng Java so với merge-base (P3, P4) | 456 | 260 |
| Ứng viên của tầng 1 | 11 | 4 |
| PR có cảnh báo mới (tầng 2) | **10** | **3** |
| Cảnh báo mới | **45** | **11** |

Tỉ lệ commit sửa Java có cảnh báo mới: 10/456 (2,2%) ở logicaldoc, 3/260 (1,2%) ở mesh. Phân bố theo luật nằm trong
[bảng đăng ký](dang-ky-pr.md): logicaldoc chủ yếu là `no-direct-response-writer` (36) và `unsafe-reflection` (7),
mesh là luật cookie (4), cảnh báo ngoài Java trong `.npmrc` (4) và luật SQL (3).

## Hai tầng có khớp nhau không

| | logicaldoc | mesh |
|---|---|---|
| Commit có cả kết quả tầng 1 và tầng 2 (`status: ok`) | 13 | 12 |
| Cùng danh sách `finding_id` | 12 | 10 |
| Tầng 1 thừa, tầng 2 ít hơn | 1 | 2 |
| Tầng 1 thiếu so với tầng 2 | 0 | 0 |

Ba ca thừa:

- mesh `95c043b02`: `jpa-sqli` trong `tests/tests-hibernate/.../MissingContentRepairTest.java`.
- mesh `4c6d8d63`: `unencrypted-socket` trong một file test được đổi tên (`tests/context-api/.../MeshOptionChanger.java`
  thành `MeshCoreOptionChanger.java`), nên đường dẫn trong dấu vân tay đổi.
- logicaldoc `7220e67d`: commit không sửa file nào trong thư mục test. Chạy lại tầng 1 riêng cho commit này cho 0
  cảnh báo mới, khớp tầng 2. Kết quả 1 của lượt quét lớn không lặp lại được. Nghi là một file bị quá trần 30 giây
  mỗi file ở phía base khi máy tải cao, nhưng **chưa kiểm chứng**: `SemgrepAdapter` không giữ danh sách lỗi của
  Semgrep.

Hai ca đầu đã xác nhận bằng cách quét riêng các file trong `test/`, `tests/`. Pipeline bỏ qua các thư mục này theo
`.semgrepignore` mặc định của Semgrep, còn tầng 1 quét tất cả. Xem
[devlog](../../../devlog/2026-11-25-loc-pr-oss-cho-cach-a.md), mục 3.

Bản đầu của tầng 1 so kết quả bằng trường `extra.lines`. Semgrep CE trả trường này là `"requires login"`, nên bản
đó bỏ sót 4 cảnh báo mới ở mesh `8d2bd4d4d` và 4 PR của logicaldoc (`-284`, `-304`, `-306`, `-538`, cộng 36 cảnh báo
mới). Bảng trên là của bản đã sửa (devlog, mục 1).

## Thời gian

| | logicaldoc | mesh |
|---|---|---|
| Tầng 1 | 2.870 giây cho 1.500 commit (1.143 commit sửa Java) | 714 giây cho 600 commit |
| Tầng 2, mỗi commit (trung vị / lớn nhất) | 686 / 850 giây | 213 / 260 giây |

Nếu chạy tầng 2 cho cả 456 commit sửa Java của logicaldoc thì mất khoảng 456 × 686 giây, tức gần 87 giờ. Lọc hai
tầng mất khoảng 48 phút cho tầng 1 cộng 2 giờ cho 11 ứng viên.

## Giới hạn

- Một lượt tầng 2 cũ (`logicaldoc 812d0d5d`, chạy với trần 300 giây) có `status: failed`. Tầng 1 cho commit này
  0 cảnh báo mới nên không chạy lại.
- Cửa sổ 600 commit của mesh trải từ 2021 tới 2026, vì nhánh `dev` của mesh có nhiều commit merge. Ba PR được chọn
  đều nằm trong giai đoạn 2025–2026.
- Tầng 1 không áp `--path-include`, `--path-exclude`. Lượt chạy này không dùng hai tham số đó.
- Kết quả của Semgrep phụ thuộc trần 30 giây mỗi file. Khi máy tải cao, một file quá trần ở phía head sẽ làm cả
  tầng 1 lẫn pipeline bỏ sót cảnh báo, còn quá trần ở phía base sinh cảnh báo "mới" giả. Chưa đo được tần suất.
