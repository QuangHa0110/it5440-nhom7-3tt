# Báo cáo hoàn tất kịch bản đánh giá — 2026-11-18

Kịch bản: thiết kế `2026-11-18-kich-ban-danh-gia-design.md` (hồ sơ `.docs/` ngoài repo). Dữ liệu: 6 repo Java mã nguồn mở và OWASP BenchmarkJava; nhãn tham chiếu do AI gán. Số liệu chi tiết: `results-2026-11-18.md` (ngoài repo). Báo cáo này chỉ chứa số liệu tổng hợp.

## Tiêu chí K — mã chạy đúng hay sai

| Mục | Kết quả | Bằng chứng |
|---|---|---|
| K1 truy vết | Có bảng ID test-plan → test; chưa có: CTX-04, LLM-07, SEC-06, SEC-09, OPS-06; một phần: 10 ca | `traceability.md` |
| K2.1 tĩnh | Ruff, format, MyPy đạt | `make check` |
| K2.2 pytest | **276 passed, 1 skipped** (live LLM, chạy riêng) tại `121fa04` | `uv run pytest` |
| K2.3 LLM thật | 2 passed (sau khi cấp khóa mới; lần đầu 401 khóa hết hạn) | `tests/llm/test_live.py` |
| K2.4 đặc tả khác mã | LLM-09 chốt: từ chối nhiều JSON object | `test_validate_rejects_two_json_objects` |
| K3 khóa manifest | Đổi một byte cấu hình chạy hoặc luật ngoài repo → `eval metrics` từ chối | `test_freeze_covers_run_config_and_external_rules` |
| K3 phiếu mù | Phiếu không chứa nhận định; phiếu kiểm định không chứa nhãn người gán chính | `test_sheets_are_blind_and_shuffled`, `test_audit_sheet_hides_primary_labels` |
| K3 số đo | Wilson, McNemar, kappa, bootstrap khớp giá trị biết trước | `tests/evaluation/test_metrics.py` |
| K4 độ bền | 60 lượt replay PR + 126 lượt quét mốc + 38 lượt B/C: **0 `failed`**; `degraded` chỉ do nhận định `invalid` | runbook B2, B5, B8 |
| K4 tất định | 3 lần chạy lại cho đúng tập 90 `finding_id` (3/3) | runbook "Hoàn thiện" |
| K5 bộ trích C | Trên `dev`: `unknown` C 30% so với B 49–58%; `invalid` C 2–10% (bằng chứng trỏ ngoài bundle) | runbook B5 |
| Jenkins J1–J6 | **Chưa làm** (tùy chọn) | — |

### Lỗi phát hiện và đã sửa

| Lỗi | Mức | Commit | Test |
|---|---|---|---|
| Test bị `.env` cục bộ ảnh hưởng | minor | `bb1b6ec` | `test_main_skips_dotenv_when_disabled` |
| Nhận nhiều JSON object (LLM-09) | major | `bb1b6ec` | `test_validate_rejects_two_json_objects` |
| Không chạy chỉ quét được | major (chặn gán nhãn mù) | `bb1b6ec` | `test_scan_only_makes_no_llm_calls` |
| Số đo không nối B/C của lượt chạy sau | major | `bb1b6ec` | `test_bc_verdicts_join_pool_after_scan_only` |
| Tách tập theo thời điểm chạy thay vì thời điểm commit | major | `bb1b6ec` | `test_build_pool_splits_by_commit_time` |
| Replay dùng số thứ tự thay số PR | minor | `bb1b6ec` | `test_plan_merged_uses_real_pr_numbers` |
| Manifest không khóa cấu hình chạy, luật ngoài repo | major | `2fed98e` | `test_freeze_covers_run_config_and_external_rules` |
| Pool lấy bản trùng theo luật đã bị gộp | major | `0812e89` | `test_pool_excludes_findings_merged_away_by_dedup` |
| Trần token mỗi lượt chạy cố định 200.000 | major | `f4204a6` | `test_budget_per_run_is_configurable` |
| GitHub App không đọc bán kính đoạn mã và trần token | major (lệch cấu hình đã khóa khi chạy App) | `121fa04` | `test_app_passes_snippet_radius_to_pipeline`, `test_settings_snippet_radius_and_budget` |

Còn mở: đầu ra LLM bị cắt cụt (`finish_reason=length`, 15/242 nhận định `eval`) — minor, cảnh báo vẫn được giữ. TD-4: App dùng một engine LLM cho cả tiến trình nên trần token cộng dồn giữa các PR — major cho vận hành dài, chưa sửa.

## Tiêu chí R — kết quả nghiên cứu

| Mục | Trạng thái | Kết quả chính |
|---|---|---|
| Pilot replay PR | Xong | 60 PR/commit → 1 cảnh báo mới; đổi sang quét mốc lịch sử (ADR 0016) |
| Pool | Xong | `dev` 84, `eval` 121 (sau gộp trùng) |
| Hiệu chuẩn người gán AI (B4) | Xong | 29/30, kappa 0,933 trên BenchmarkJava |
| Nhãn `dev`/`eval` | Xong | `eval`: 13 Thật, 99 Sai, 9 KXĐ |
| Kiểm định 50 ca | Xong bằng subagent AI (ADR 0017) | kappa 0,613; **không có kiểm định người** |
| Chỉnh trên `dev`, khóa | Xong | B bán kính 40, hiển thị C, tag `eval-freeze-1` |
| A/B/C trên `eval` | Xong | B 74%, C 74% FP-removal; TP-loss 0/13; McNemar p = 1,0; FP nền 88% |
| Độ ổn định | Xong | đổi nhãn qua 3 lần: B 12%, C 22% (n = 90) |
| D2 BenchmarkJava | Xong | B 69%, C 92% FP-removal; TP-loss 1/89, 3/89; McNemar p ≈ 9e-06 |
| D3 Vul4J (RQ4) | **Chưa làm** | — |
| D4 PR trên fork (RQ3 mô tả) | Xong (2026-11-19) | 6 PR trên fork Roller qua GitHub App: mở PR → xong trung vị 80 s, tối đa 94 s; 65.110 token; 2 lỗi cố ý được B và C giữ; không cảnh báo thừa ở PR an toàn/tài liệu; 1 ca bộ quét bỏ sót |
| Mốc RQ3 lịch sử (`--side first`) | **Chưa làm** | — |
| Kết luận "đáng dùng" | — | **Chưa đủ bằng chứng**: FP-removal 74% (đạt), thời gian trên PR 80 s (đạt, D4), nhưng cận trên TP-loss 23% > 10% và chưa có ngân sách chi phí |

## Cổng 5.7 (trước `freeze`)

| Điều kiện | Trạng thái |
|---|---|
| K2.1, K2.2 pass; K2.4 chốt | Đạt |
| Không blocker; major đã sửa hoặc ghi giới hạn | Đạt (major phát hiện sau `freeze` — pool, trần token — đã sửa và chạy lại phần bị ảnh hưởng) |
| K3: dấu vân tay ổn định, phiếu mù, khóa manifest, số đo | Đạt, trừ dấu vân tay trên commit chỉ reformat ở repo thật (đã có test trên fixture, chưa đo trên repo thật) |
| K4: `failed` ≤ 5%, tất định 100% | Đạt (0% failed; tất định 3/3) |
| K5 báo cáo; quyết định ADR 0003 D6 | `missing`/`unknown` của C trên `dev` 30% < 50% → không cần Joern |
