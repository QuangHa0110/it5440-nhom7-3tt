# Lọc PR trên repo Java mã nguồn mở cho cách A: những điều bất ngờ

- **Ngày:** 2026-11-25. Kế hoạch [P17](../plans/active/2026-11-25-p17-thu-du-lieu-oss-sonnh.md), bước 3 của
  [hướng dẫn chọn repo và PR](../huong-dan-chon-repo-va-pr.md).

> Ghi chú 2026-11-25: kế hoạch P17 đã đóng, nay ở [`plans/done/`](../plans/done/2026-11-25-p17-thu-du-lieu-oss-sonnh.md).

## 1. Semgrep CE trả `"requires login"` thay cho đoạn mã 🟡

**Phát hiện.** Trong JSON của `semgrep scan --json` (CE 1.185.0, không đăng nhập), trường `extra.lines` của mọi kết
quả là chuỗi `"requires login"` (473/473 kết quả trong một lượt quét mesh), không phải dòng mã bị báo.

**Vì sao quan trọng.** Script nào so khớp cảnh báo bằng trường này (sàng nhanh, so head với base, gộp kết quả bằng
tay) sẽ ngầm chỉ so **số lượng** cảnh báo theo cặp (file, luật). Bản đầu của bộ sàng trong `scripts/filter_prs.py`
mắc đúng lỗi này. Nó bỏ sót commit `8d2bd4d4` của gentics/mesh, nơi 4 cảnh báo cookie là mới theo pipeline vì
đoạn mã ở dòng bị báo đã đổi, trong khi số cảnh báo của file vẫn giữ nguyên. Pipeline không bị ảnh hưởng: nó đọc
SARIF và lấy đoạn mã từ file (`scan/semgrep.py`, `_with_snippet`).

**Đề xuất điều chỉnh.** Script mới làm việc với kết quả Semgrep nên gọi lại `SemgrepAdapter` và `to_findings`,
không tự đọc JSON. `filter_prs.py` đã sửa theo cách này (commit `fix(scripts)`).

## 2. `replay` quá chậm để lọc PR trên repo lớn, mà phần lớn commit không có cảnh báo mới 🟡

**Phát hiện.** `pr-triage replay` quét toàn repo hai lần cho mỗi commit (head và merge-base), không có cache. Trên
repo khoảng 300 nghìn dòng, chạy trên máy dùng chung, mỗi commit mất 3–11 phút. Phần lớn commit không sinh cảnh báo
mới với `p/default`. Ở gentics/mesh, trong 600 commit first-parent gần nhất có 260 commit sửa Java (P3, P4), nhưng
chỉ 4 commit có cảnh báo mới. Ở 10 commit đầu tiên chạy bằng pipeline đầy đủ, không commit nào có cảnh báo mới.

**Vì sao quan trọng.** Chỉ tiêu mỗi thành viên là 20 cảnh báo mới. Với mật độ như trên, phải xét lùi hàng trăm tới
hơn một nghìn commit. Chạy `replay` tuần tự cho chừng đó commit mất nhiều ngày.

**Đề xuất điều chỉnh.** Lọc hai tầng bằng `scripts/filter_prs.py`. Luật Semgrep CE chỉ phân tích trong một file,
nên cảnh báo mới chỉ có thể nằm ở file mà commit sửa. Tầng 1 quét chung một lượt các file thay đổi (ở merge-base và
ở head) của mọi commit, rồi tính cảnh báo mới bằng đúng các bước của pipeline. Tầng 2 chạy pipeline đầy đủ chỉ
trên các ứng viên, và số liệu chính thức lấy từ tầng 2. Kiểm chứng trên mesh: ở 11 commit đã chạy pipeline đầy đủ,
10 commit cho cùng danh sách `finding_id` với bộ sàng. Ở commit còn lại, bộ sàng thừa một cảnh báo (mục 3).

## 3. Cảnh báo trong thư mục `test/`, `tests/` không bao giờ được tính 🟢

**Phát hiện.** Repo không có `.semgrepignore` thì Semgrep tự áp danh sách bỏ qua mặc định, trong đó có các thư mục
`test/` và `tests/`. Pipeline quét bản export của repo nên chịu quy tắc này. Ở mesh, file
`tests/tests-hibernate/src/main/java/.../MissingContentRepairTest.java` có cảnh báo `jpa-sqli` khi quét riêng file,
nhưng pipeline không báo. Bộ sàng quét với `.semgrepignore` rỗng nên vẫn thấy cảnh báo này.

**Vì sao quan trọng.** Đây đúng là điều ta muốn (mã test không chạy trên production), nhưng cần ghi vào phần giới
hạn của số liệu A. Repo đặt mã sản phẩm dưới thư mục tên `test` hay `tests` sẽ bị đếm thiếu mà không báo lỗi gì.

**Đề xuất điều chỉnh.** Khi chọn repo, kiểm tra cấu trúc thư mục. Không đổi pipeline.
