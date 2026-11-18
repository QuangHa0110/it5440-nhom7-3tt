# Kịch bản demo

Mục tiêu: cho người xem thấy bot **phát hiện**, **lọc bớt cảnh báo sai**, **không bị lừa**, và **nói thật về giới hạn**. Thời lượng khoảng 10 phút.

## Chuẩn bị

1. Tải bộ luật Semgrep đã khóa (`python scripts/fetch_semgrep_rules.py --frozen`, ADR 0015), rồi cài App theo [github-app.md](github-app.md) và chạy máy chủ.
2. Tạo một repo **trống** trên GitHub (ví dụ `OWNER/pr-triage-demo`), cài App lên repo đó.
3. Dựng và đẩy bộ demo:

```bash
python scripts/demo_repo.py --workdir /tmp/pr-triage-demo --repo OWNER/pr-triage-demo
```

Muốn xem thử mà chưa đụng GitHub: thêm `--dry-run` thay cho `--repo`. Script tạo nhánh `main` sạch (kèm `.pr-triage.yml`) và sáu nhánh `demo/...`, mỗi nhánh một PR.

Để đóng vai bên outsource, mở PR từ một tài khoản khác hoặc từ một fork. Bot hoạt động giống nhau.

## Sáu PR và điều cần thấy

Cột "Công cụ quét" là kết quả chạy ngày 2026-11-19 với bộ `p/default` đã khóa, sau khi gộp các luật trùng (khoảng 19 giây mỗi PR, quét cả nhánh đích và nhánh PR). Cột "Kỳ vọng" là điều bot cần làm sau khi LLM nhận định.

| PR | Thay đổi | Công cụ quét (cảnh báo mới) | Kỳ vọng |
|---|---|---|---|
| 01 SQL injection | Nối tham số `name` vào câu truy vấn | CWE-89 `UserDao.java:28` (hai luật `formatted-sql-string` và `jdbc-sqli` gộp làm một). CWE-79 `UserController.java:30` | Cảnh báo CWE-89 kèm giải thích đường đi của dữ liệu. Check run có chú thích đúng dòng. CC tác giả vì mức `high` |
| 02 Truy vấn có tham số | Cùng chức năng PR 01, dùng `PreparedStatement` | Chỉ CWE-79 `UserController.java:30` | **Không có cảnh báo SQL injection.** Mã trông giống PR 01 nhưng truy vấn an toàn. Cảnh báo XSS còn lại là thật ở mức công cụ: kết quả truy vấn được in thẳng ra response |
| 03 Chú thích cố lừa bot | PR 01 kèm chú thích "bỏ qua mọi chỉ dẫn", `@everyone`, một liên kết | Như PR 01 (CWE-89 ở dòng 31) | Bot vẫn báo. Comment không có `@mention` nào kích hoạt, liên kết bị vô hiệu |
| 04 Secret trong mã | Khóa truy cập và mật khẩu viết cứng | Hai CWE-798 ở `Config.java:7` và `:8` (bộ quét secret) | Hai cảnh báo CWE-798, giá trị đã được che. Dòng đọc biến môi trường không bị báo |
| 05 Thay đổi vô hại | Thêm một hàm không liên quan | Không có | "Không có cảnh báo mới" và dòng nhắc rằng điều đó không có nghĩa là mã an toàn |
| 06 Ép kiểu số nguyên | Nối chuỗi nhưng giá trị luôn là số nguyên | CWE-89 `UserDao.java:27`, luật `jdbc-sqli` (độ tin cậy LOW) | LLM nhận ra giá trị an toàn và thu gọn cảnh báo (phụ thuộc mô hình) |

Cảnh báo XSS ở `UserController.java:30` xuất hiện từ khi đổi sang `p/default`: nhánh `main` có cùng mẫu ở dòng 20 nên dòng đó không bị tính là mới, còn hàm `doPost` mà PR 01 đến 03 thêm vào thì có.

## Gợi ý lời dẫn

1. **PR 01.** "Đây là cảnh báo thật. Chú ý bot không chặn merge, chỉ báo ngay trong PR trước khi ai đó bấm merge."
2. **PR 02 và 06.** "Bot không báo bừa. Mã an toàn thì im lặng, mã công cụ nghi ngờ nhưng thật ra ổn thì được thu gọn. Đây là phần LLM mang lại so với công cụ quét thuần."
3. **PR 03.** "Với team bên ngoài, mã có thể cố lừa cả bot. Mô hình không có công cụ, nội dung nó sinh ra được làm sạch, và nhãn 'sai' chỉ thu gọn cảnh báo chứ không xóa."
4. **Phản hồi.** Dưới PR 01 trả lời `fp <mã>` bằng tài khoản tác giả. Với cấu hình demo (`trusted_roles: [reviewer]`), cảnh báo **không** bị coi là đã đánh dấu sai. Trả lời lại bằng tài khoản có quyền review thì mới tính.
5. **Sửa lỗi.** Đẩy một commit sửa PR 01 (đổi sang truy vấn có tham số). Lượt chạy sau cập nhật comment, và cảnh báo cũ được ghi nhận là đã sửa (xem `GET /stats`).

## Nói thật về giới hạn

Bot **không** tìm "mã độc". Nó lọc cảnh báo của công cụ quét, nên lỗi mà luật quét không định nghĩa thì bot không thấy. Bộ luật hiện là `p/default` của Semgrep (118 luật Java, ADR 0015), cộng quét secret. Backdoor có chủ đích, logic bomb hay lệnh tải mã từ ngoài, nếu không khớp luật, sẽ không được báo. Nêu rõ điều này làm demo đáng tin hơn.

## Dọn dẹp

Gỡ cài đặt App khỏi repo demo và xóa repo. Xóa `secrets/` và `app-manifest.html` nếu không dùng nữa.
