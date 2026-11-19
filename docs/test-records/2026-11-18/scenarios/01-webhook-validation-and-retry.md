# Kịch bản 01 — Webhook validation và retry

| Trường | Nội dung |
|---|---|
| Mục tiêu | Xác minh kiểm tra chữ ký, giới hạn repo, lọc draft và chống xử lý lặp delivery. |
| Môi trường | POST payload tổng hợp đã ký trực tiếp vào webhook đang chạy; không tạo PR GitHub mới cho các ca này. |
| Kết quả mong đợi | Chữ ký sai bị từ chối; repo ngoài allowlist và PR draft bị bỏ qua; lần gửi lặp cùng delivery ID không tạo job lần hai. |

## Ca kiểm thử và kết quả

| Ca | Kết quả quan sát | Đạt? |
|---|---|---|
| Chữ ký HMAC sai | HTTP `401`, chữ ký không hợp lệ | Đạt |
| Repository không nằm trong allowlist | HTTP `200`, `ignored: true`; không được đưa vào triage | Đạt |
| PR draft của repo cho phép | HTTP `200`, `ignored: "PR nháp"` | Đạt |
| Payload `closed` tổng hợp với delivery ID mới, gửi lần đầu | HTTP `202`, job được xếp hàng; không có run trước nên job kết thúc `skipped` | Đạt |
| Gửi lại chính payload với cùng delivery ID | HTTP `200`, `duplicate: true` | Đạt |

**Kết luận:** Đạt cho các nhánh webhook đã nêu. Ca duplicate dùng payload tổng hợp; ngoài ra các sự kiện PR/feedback thật trong PR #1–#3 cũng được tiếp nhận qua GitHub.
