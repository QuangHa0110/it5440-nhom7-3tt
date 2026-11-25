# `docs/plans/` — vòng đời kế hoạch

Kế hoạch là một đơn vị công việc có thể commit, với điều kiện hoàn thành quan sát được. Thư mục cho biết trạng thái, nên trả lời "đang làm gì" bằng `ls`.

| Bucket | Ý nghĩa | Ai chuyển, khi nào |
|---|---|---|
| `queued/` | Sẵn sàng chạy, có thứ tự. Chưa ai làm | Tác giả, khi viết xong |
| `active/` | Đang có người làm. Mỗi kế hoạch một người nhận | Người làm, khi bắt đầu |
| `done/` | Xong, điều kiện hoàn thành đã được kiểm chứng | Người làm, ở commit đóng |
| `failed/` | Bỏ dở hoặc bị thay thế, giữ lại kèm lý do | Người làm, khi dừng |

- Tên: `YYYY-MM-DD-<slug>.md` (hoặc thư mục cùng tên nếu có tài liệu kèm). Bắt đầu từ [_template.md](_template.md).
- Chuyển bucket bằng `git mv`, không sao chép.
- `done/` và `failed/` là hồ sơ lịch sử: chú thích bằng ghi chú có ngày, không viết lại phần thân.
- Công cụ Claude Code ghi kế hoạch mới vào `queued/` (xem `.claude/settings.json`), người làm chuyển tay sang `active/`.
- Cần kế hoạch khi việc có từ 3 task trở lên.

## Các đợt đã hoàn thành

- [P01–P07](done/) đặt nền tảng cho luồng quét, phân loại, phản hồi và đánh giá ngoại tuyến.
- [P08–P12](done/) bổ sung quét secret, cấu hình theo repo, GitHub App và bộ demo.
- [P13](done/2026-11-17-p13-jenkins-job-trung-tam-nhieu-repo.md) bổ sung job Jenkins trung tâm.
- [P14](done/2026-11-20-p14-hai-duong-kich-hoat-huong-doi-tuong.md) dùng chung lõi cho GitHub App và Jenkins.
- [P16](done/2026-11-22-p16-nha-cung-cap-scm.md) thêm GitLab, Gitea, Bitbucket Server qua lớp nhà cung cấp SCM.
- [P15](done/2026-11-19-p15-semgrep-bo-luat-co-san.md) thay luật tự viết bằng bộ luật Semgrep `p/default` khóa bằng mã băm.
- [P17](done/2026-11-25-p17-thu-du-lieu-oss-sonnh.md) lọc PR bằng A và chạy A, B, C trên hai repo Java mã nguồn mở (phần của sonnh).

## Quy tắc chạy xuyên đêm

Áp dụng khi người dùng giao cho Claude Code chạy các kế hoạch trên mà không có mặt.

1. Mỗi kế hoạch một nhánh cá nhân tách từ `dev` cục bộ, mỗi task một commit. **Không push, không mở PR.**
2. Cổng của kế hoạch qua thì `git mv` sang `done/` và ghi mục Kết quả. Chưa qua thì để ở `active/`.
3. Gặp điều bất ngờ hoặc kết quả đo làm lung lay một ADR thì ghi vào `docs/devlog/` rồi đi tiếp bằng phương án an toàn. Không tự sửa ADR đã `accepted`.
4. **Dừng và để lại ghi chú** khi: cần quyết định không có trong ADR, cổng LLM không dùng được sau 3 lần thử cách nhau, một task lỗi sau 3 lần sửa, hoặc phải chạm vào thứ nằm ngoài repo.
5. Khóa API chỉ lấy từ biến môi trường. Không ghi vào file, log, commit hay devlog.
6. Không gửi mã của công ty Z tới cổng LLM ngoài. Dữ liệu thử là mã nguồn mở công khai. (Bot chạy trên hạ tầng của Z được dùng LLM cloud theo [ADR 0020](../adr/0020-gui-ma-cua-z-len-llm-cloud.md). Quy tắc này chỉ áp dụng cho phiên Claude Code chạy không có người giám sát.)
7. Cuối phiên viết bản tóm tắt vào `docs/devlog/` gồm: đã xong, đang dở, các quyết định tự đưa ra, lệnh để tái chạy.
