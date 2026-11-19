# Kiểm thử ngày 2026-11-17

## Phạm vi

Kiểm thử end-to-end trên repo công khai `vudinhminh08/task-manager-project`, dùng GitHub App, webhook, Semgrep và pipeline LLM đã cấu hình. Các PR chỉ phục vụ thử nghiệm; không PR nào được merge.

## Kịch bản

- [SQL injection thật](scenarios/01-sql-injection-positive.md)
- [PR nháp và thay đổi sạch](scenarios/02-draft-and-clean-pr.md)
- [SQL nối chuỗi an toàn nhờ allowlist](scenarios/03-allowlist-false-positive.md)

## Kết quả và người thực hiện

- [Tổng hợp kết quả](results/e2e-results.md)
- [Người thực hiện và người yêu cầu](testers/tester-record.md)
