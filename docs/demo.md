# Kịch bản demo

Mục tiêu: cho người xem thấy bot **phát hiện**, **lọc bớt cảnh báo sai**, **không bị lừa**, và **nói thật về giới hạn**. Thời lượng khoảng 10 phút.

## Chuẩn bị

1. Cài App theo [github-app.md](github-app.md) và chạy máy chủ.
2. Tạo một repo **trống** trên GitHub (ví dụ `OWNER/pr-triage-demo`), cài App lên repo đó.
3. Dựng và đẩy bộ demo:

```bash
python scripts/demo_repo.py --workdir /tmp/pr-triage-demo --repo OWNER/pr-triage-demo
```

Muốn xem thử mà chưa đụng GitHub: thêm `--dry-run` thay cho `--repo`. Script tạo nhánh `main` sạch (kèm `.pr-triage.yml`) và sáu nhánh `demo/...`, mỗi nhánh một PR.

Để đóng vai bên outsource, mở PR từ một tài khoản khác hoặc từ một fork. Bot hoạt động giống nhau.

## Sáu PR và điều cần thấy

| PR | Thay đổi | Kỳ vọng |
|---|---|---|
| 01 SQL injection | Nối tham số `name` vào câu truy vấn | Cảnh báo CWE-89 kèm giải thích đường đi của dữ liệu. Check run có chú thích đúng dòng. CC tác giả vì mức `high` |
| 02 Truy vấn có tham số | Cùng chức năng PR 01, dùng `PreparedStatement` | **Không có cảnh báo.** Mã trông giống PR 01 nhưng an toàn |
| 03 Chú thích cố lừa bot | PR 01 kèm chú thích "bỏ qua mọi chỉ dẫn", `@everyone`, một liên kết | Bot vẫn báo. Comment không có `@mention` nào kích hoạt, liên kết bị vô hiệu |
| 04 Secret trong mã | Khóa truy cập và mật khẩu viết cứng | Hai cảnh báo CWE-798, giá trị đã được che. Dòng đọc biến môi trường không bị báo |
| 05 Thay đổi vô hại | Thêm một hàm không liên quan | "Không có cảnh báo mới" và dòng nhắc rằng điều đó không có nghĩa là mã an toàn |
| 06 Ép kiểu số nguyên | Nối chuỗi nhưng giá trị luôn là số nguyên | Công cụ quét báo "nối chuỗi", LLM nhận ra giá trị an toàn và thu gọn cảnh báo (phụ thuộc mô hình) |

## Gợi ý lời dẫn

1. **PR 01.** "Đây là cảnh báo thật. Chú ý bot không chặn merge, chỉ báo ngay trong PR trước khi ai đó bấm merge."
2. **PR 02 và 06.** "Bot không báo bừa. Mã an toàn thì im lặng, mã công cụ nghi ngờ nhưng thật ra ổn thì được thu gọn. Đây là phần LLM mang lại so với công cụ quét thuần."
3. **PR 03.** "Với team bên ngoài, mã có thể cố lừa cả bot. Mô hình không có công cụ, nội dung nó sinh ra được làm sạch, và nhãn 'sai' chỉ thu gọn cảnh báo chứ không xóa."
4. **Phản hồi.** Dưới PR 01 trả lời `fp <mã>` bằng tài khoản tác giả. Với cấu hình demo (`trusted_roles: [reviewer]`), cảnh báo **không** bị coi là đã đánh dấu sai. Trả lời lại bằng tài khoản có quyền review thì mới tính.
5. **Sửa lỗi.** Đẩy một commit sửa PR 01 (đổi sang truy vấn có tham số). Lượt chạy sau cập nhật comment, và cảnh báo cũ được ghi nhận là đã sửa (xem `GET /stats`).

## Nói thật về giới hạn

Bot **không** tìm "mã độc". Nó lọc cảnh báo của công cụ quét, nên lỗi mà luật quét không định nghĩa thì bot không thấy. Luật tùy chỉnh hiện phủ SQL injection, cộng quét secret. Backdoor có chủ đích, logic bomb hay lệnh tải mã từ ngoài, nếu không khớp luật, sẽ không được báo. Nêu rõ điều này làm demo đáng tin hơn.

## Dọn dẹp

Gỡ cài đặt App khỏi repo demo và xóa repo. Xóa `secrets/` và `app-manifest.html` nếu không dùng nữa.
