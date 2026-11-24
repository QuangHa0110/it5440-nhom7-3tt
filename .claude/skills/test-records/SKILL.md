---
name: test-records
description: Ghi hồ sơ kiểm thử thủ công hoặc đợt đánh giá vào docs/test-records/<ngày>/ đúng quy ước. Dùng khi chạy kịch bản test tay, e2e thật, đánh giá OSS, hoặc khi người dùng nói "ghi hồ sơ test", "lưu kết quả kiểm thử".
---

# Ghi hồ sơ kiểm thử

Hai nơi khác nhau, không lẫn:

- `tests/`: mã pytest tự động, phản chiếu `src/`, chạy bằng `make check`.
- `docs/test-records/`: hồ sơ kiểm thử **thủ công** theo ngày. Không chứa mã test.

## Cấu trúc

```
docs/test-records/<YYYY-MM-DD>/        # múi giờ Asia/Ho_Chi_Minh
  README.md                            # tóm tắt ngày, liên kết tới các mục dưới
  scenarios/NN-<tên>.md                # mục tiêu, tiền điều kiện, kết quả mong đợi, kết quả thực tế
  results/<tên>.md                     # tổng hợp, số liệu, giới hạn kiểm thử
  testers/tester-record.md             # người thực hiện, người yêu cầu, người xác nhận
```

## Các bước

1. Tạo thư mục ngày nếu chưa có; không sửa hồ sơ ngày cũ (chỉ thêm "Đính chính" có ngày).
2. Viết kịch bản trước khi chạy; ghi kết quả thực tế sau, kể cả khi thất bại hoặc bị bỏ qua.
3. Ghi rõ cái **chưa kiểm chứng** và giới hạn (nhãn do AI gán, mẫu nhỏ, mô hình có thể đã thấy dữ liệu).
4. Thêm một dòng vào mục "Hồ sơ đã ghi" của `docs/test-records/README.md`.
5. Dùng đường dẫn tương đối hoặc bắt đầu từ `docs/test-records/`; không dùng đường dẫn máy cá nhân.

## Không bao giờ lưu

API key, webhook secret, private key, SARIF thô, dữ liệu nhạy cảm của công ty Z.
