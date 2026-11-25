# Kịch bản: A/B/C trên repo jivejdon

## Mục tiêu

Đo cách bot lọc cảnh báo của Semgrep trên các thay đổi thật của một ứng dụng Java mã nguồn mở: A (chỉ Semgrep), B (LLM + vài dòng mã quanh vị trí báo), C (LLM + ngữ cảnh luồng dữ liệu). B và C xét cùng tập cảnh báo của A.

## Dữ liệu

| Mục | Giá trị |
|---|---|
| Repo | [banq/jivejdon](https://github.com/banq/jivejdon), diễn đàn web Java (Servlet/JSP, JDBC), Apache-2.0 |
| Quy mô | 555 file Java, khoảng 54.900 dòng (không tính test), tại `8df5eb50` |
| Mức độ biết đến | 583 sao (2026-11-25) |
| Đơn vị "PR" | Repo commit thẳng lên `master`, gần như không có PR. Mỗi commit là một "PR": base = cha thứ nhất, head = commit (hướng dẫn P2) |

Lý do chọn: ứng dụng chạy thật, nhận đầu vào HTTP, ghi log, truy vấn CSDL, chuyển hướng (R4); ít nổi tiếng (R6), cỡ vừa (R9), không thuộc danh sách loại trừ. Đã thử và loại: roller, jspwiki, openmrs-core (thuộc danh sách loại trừ, ít cảnh báo mới); apache/syncope (2 commit có cảnh báo từ 2025-05, cả hai diff trên 1.000 dòng).

## Cấu hình

| Mục | Giá trị |
|---|---|
| Mã pr-triage | `origin/main` @ `81929df` |
| Semgrep | CE 1.185.0, bộ `p/default` 1.074 luật, khớp `configs/semgrep/rulesets.lock` (sha256 `9c76333a…`) |
| **Mô hình LLM** | **Claude Sonnet 5.5 (`claude-sonnet-5-5`), effort `medium`** |
| Cách gọi LLM | Cầu nối cục bộ tương thích OpenAI, mỗi lời gọi chạy `claude -p` một lượt: không công cụ (`--tools ""`), system prompt của bot (`--system-prompt-file`), không MCP, không nạp CLAUDE.md hay cài đặt (`--setting-sources ""`), không lưu phiên |
| Tham số `run` | `--variants B,C --no-secrets --budget-pr-tokens 400000`; bán kính B và prompt để mặc định; hiển thị mặc định theo B (`--display B`): chỉ cảnh báo B gán `likely_false` bị thu gọn trong comment |

## Các bước

1. **Lọc ứng viên bằng A, không gọi LLM.** Quét Semgrep chỉ các file Java đã đổi ở base và head của 1.133 commit (từ 2018) có sửa Java. Semgrep CE phân tích trong từng file nên cảnh báo mới chỉ nằm ở file đổi. Kiểm chứng cách lọc này trên jspwiki: bắt đủ 4/4 PR mà `pr-triage run` xác nhận.
2. **Xác nhận bằng `pr-triage run --variants none`** trên từng ứng viên. Giữ commit có cảnh báo mới, diff dưới 1.000 dòng (P4), có sửa mã Java, không phải merge nhánh cục bộ (P3).
3. **Chốt danh sách** 18 commit, 30 cảnh báo (28 trong file Java). Người yêu cầu duyệt trước khi chạy B/C (P6).
4. **Chạy `pr-triage run --variants B,C`** cho từng commit.

## Kết quả mong đợi

- Mọi lượt chạy `status=ok`, không lỗi gọi LLM, không `unknown` do trần token.
- Mỗi cảnh báo có đúng một nhận định B và một nhận định C.
- Số cảnh báo A khớp bảng đăng ký.

Kết quả thực tế: [results/04-ket-qua-jivejdon.md](../results/04-ket-qua-jivejdon.md).
