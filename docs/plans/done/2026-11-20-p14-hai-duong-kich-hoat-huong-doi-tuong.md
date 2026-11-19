# P14. Hai đường kích hoạt dùng chung lõi, thiết kế hướng đối tượng

- **Status:** done
- **Người làm:** trinq (với Claude Code, chạy xuyên đêm)
- **Đóng:** [ADR 0018](../../adr/0018-hai-duong-kich-hoat-mot-loi-moi-repo-mot-duong.md)
- **Quyết định cho phép:** ADR 0018
- **Nhánh:** `trinq/arch/trigger-adapters`
- **Bắt đầu / Kết thúc:** 2026-11-20 / 2026-11-20

---

## Bối cảnh

Xem ADR 0018: hai bản danh sách cho phép lệch nghĩa, logic Jenkins không có test, không chặn được một repo bị quét bởi cả hai đường.

## Ngoài phạm vi

- Không tách ba job theo quyền cho Jenkins (ADR 0007, nợ TD-5).
- Không đổi lõi quét, LLM, lược đồ lưu trữ.
- Không chạy Jenkins thật, không gọi LLM thật (chưa có khóa trong môi trường).

## Hiện trạng đã kiểm chứng

- 2026-11-20: `dev` gộp P13, `make test` qua 276 test, 1 bị bỏ qua (test LLM thật).

---

## Task

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | `core/delivery.py`: `Channel`, `ScanRequest`, `RepoAllowList`, `RoutePolicy`, `RepoGate` | `tests/core/test_delivery.py` qua | — |
| T2 | Gói `triggers/`: `Trigger` (lớp trừu tượng) và `JenkinsParamsTrigger`, `PollTrigger`, `PollState`, `GitHubPullLister` | `tests/triggers/` qua | T1 |
| T3 | `app/trigger.py`: `GitHubWebhookTrigger`; `Settings` và `server.py` dùng `RepoGate` | `tests/app/` qua, repo sai kênh nhận `{"ignored": true}` | T1, T2 |
| T4 | `bot/sinks.py`: `ResultSink`, `ConsoleSink`, `ScmSink`; CLI `publish` và `handle_triage` dùng sink | `tests/bot/test_sinks.py` qua | — |
| T5 | CLI `pr-triage ci allowed\|poll`; Jenkinsfile, Dockerfile, README bỏ `ci_helper.py` | `grep -r ci_helper` rỗng; test CLI qua | T2 |
| T6 | Ranh giới import, tài liệu, nợ | `make check` qua | T1–T5 |

## Cổng

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì khi xảy ra |
|---|---|---|
| Sửa file của PR #7 (Jenkins) gây xung đột khi tác giả đẩy thêm | Merge báo xung đột ở `deploy/jenkins/` | Thông báo tác giả, hợp nhất tay |
| Đổi nghĩa "rỗng" làm App đổi hành vi | Test `tests/app` đỏ | Giữ `empty_allows_all=True` cho App |
