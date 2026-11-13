# ADR 0011 — Dấu vân tay cảnh báo không dùng số dòng, cảnh báo mới là head trừ base

- **Status:** proposed (2026-11-13)
- **Người quyết định:** trinq
- **Liên quan:** [architecture.md](../architecture.md) mục 7.1; proposal 3.1, 7.2

## Bối cảnh

Đơn vị phân tích của RQ1 và RQ2 là cảnh báo duy nhất. Số dòng đổi khi mã phía trên bị thêm bớt, nên nếu dấu vân tay dùng số dòng thì một cảnh báo cũ sẽ bị tính là mới ở mỗi commit. Bài phần mềm vệ tinh [1] dùng dấu vân tay để khử trùng lặp. Không phải công cụ quét nào cũng có chế độ quét theo diff.

## Quyết định

- **D1.** Dấu vân tay là SHA-256 của: mã luật đã chuẩn hóa, đường dẫn tương đối, tên đầy đủ của hàm bao quanh, đoạn mã khớp đã bỏ khoảng trắng, và số thứ tự của lần khớp trong hàm. Không dùng số dòng. `finding_id` là 12 ký tự hex đầu.
- **D2.** Cảnh báo mới của một PR là tập dấu vân tay ở bản head trừ tập ở bản merge-base. Pipeline quét cả hai bản.
- **D3.** Hai cảnh báo cùng CWE, cùng file, cùng hàm và có vùng sink chồng nhau được gộp thành một cảnh báo duy nhất có nhiều nguồn.
- **D4.** Khi không xác định được hàm bao quanh, dùng cửa sổ đoạn mã khớp cộng hai dòng xung quanh làm thay thế và ghi cờ `no_symbol`.
- **D5.** Có bộ test cho các commit chỉ đổi định dạng và chỉ thêm dòng phía trên, khẳng định dấu vân tay không đổi.

## Phương án khác

- **Dấu vân tay của công cụ quét (ví dụ `partialFingerprints` của Semgrep):** tiện nhưng khác nhau giữa công cụ và không đảm bảo ổn định giữa phiên bản.
- **Quét theo diff của công cụ:** nhanh hơn nhưng không dùng được cho mọi công cụ và khó tái lập mốc base.

## Hệ quả

- **Tốt hơn:** cùng một cách tính cho mọi công cụ, ổn định trước thay đổi vị trí.
- **Tệ hơn:** quét hai lần mỗi PR. Một đổi tên hàm sẽ làm cảnh báo bị tính là mới.
- **Từ nay phải đúng:** thuật toán dấu vân tay đổi thì phải thêm phiên bản vào dấu vân tay, vì nó là khóa của cache và của toàn bộ số liệu.
