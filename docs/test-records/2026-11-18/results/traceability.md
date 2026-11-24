# Truy vết ca kiểm thử → bằng chứng (K1) — 2026-11-18

Đối chiếu ID trong test-plan (`.docs/quality/testing/test-plan.md`, ngoài repo) với test tự động và hồ sơ E2E. Mốc mã: commit `bb1b6ec`.

**Cách đọc:**

- **Có:** tên và phạm vi test khớp oracle của ca.
- **Một phần:** test chạm đúng chủ đề nhưng chưa chắc khẳng định đủ oracle; cần đọc thân test hoặc thêm ca.
- **E2E:** chỉ có bằng chứng thủ công (`2026-11-17/results/e2e-results.md`).
- **Chưa có:** không tìm thấy bằng chứng.

Lần chạy: `make check` → 268 passed, 1 skipped (`tests/llm/test_live.py`). Chạy riêng live test với biến môi trường: **2 failed, HTTP 401 "API key expired"** — xem mục cuối.

## Scanner và fixture (SCN)

| ID | Bằng chứng | Mức |
|---|---|---|
| SCN-01 | `test_demo_kit.py::test_scenario_behaves_as_documented`; E2E PR #1 | Có |
| SCN-02 | `test_demo_kit.py::test_scenario_behaves_as_documented` | Có |
| SCN-03 | `test_demo_kit.py::test_prompt_injection_scenario_cannot_trigger_mentions` | Có |
| SCN-04 | `test_demo_kit.py::test_scenario_behaves_as_documented`; `scan/test_secrets.py::test_scanner_finds_and_never_keeps_the_value` | Có |
| SCN-05 | `test_demo_kit.py`; `bot/test_bot.py::test_render_failed_empty_degraded_never_says_safe`; E2E PR #2 | Có |
| SCN-06 | `test_demo_kit.py::test_scenario_behaves_as_documented`; E2E PR #3 | Có |
| SCN-07 | `pipeline/test_runner.py::test_no_new_findings_when_base_already_has_it` (không phải PR chỉ sửa README) | Một phần |
| SCN-08 | `scan/test_semgrep_adapter.py::test_timeout_raises`; `pipeline/test_runner.py::test_scan_failure_marks_run_failed`; `app/test_flow.py::test_failure_is_recorded_and_reported_without_claiming_safe` | Có |

## Chuẩn hóa (NRM)

| ID | Bằng chứng | Mức |
|---|---|---|
| NRM-01 | `normalize/test_ops.py::test_dedup_merges_overlapping_same_cwe_symbol` | Có |
| NRM-02 | `normalize/test_ops.py::test_dedup_keeps_apart_different_symbols_or_no_cwe` (khác CWE cùng vị trí chưa rõ) | Một phần |
| NRM-03 | `pipeline/test_runner.py::test_no_new_findings_when_base_already_has_it` | Có |
| NRM-04 | `normalize/test_ops.py::test_new_findings_detects_added_vulnerability` | Có |
| NRM-05 | `normalize/test_ops.py::test_new_findings_stable_when_lines_added_above`; `core/test_fingerprint.py::test_stable_across_formatting_and_comments` | Có (trên fixture; cần đo lại trên repo thật ở K3) |
| NRM-06 | `pipeline/test_policy_filter.py::test_pipeline_filter_and_hidden_note`; `pipeline/test_repoconfig_globs.py::test_globs` | Có |

## Ngữ cảnh (CTX)

| ID | Bằng chứng | Mức |
|---|---|---|
| CTX-01 | `context/test_dataflow.py::test_direct_flow_in_same_function`; `llm/test_redact_prompt_schema.py::test_snippet_provider_reads_window` | Có |
| CTX-02 | `context/test_dataflow.py::test_cross_file_flow_found_through_caller` (khác file; cùng file khác hàm chưa có ca riêng) | Một phần |
| CTX-03 | `context/test_dataflow.py::test_cross_file_flow_found_through_caller` | Có |
| CTX-04 | Không có ca riêng cho sanitizer ứng viên | Chưa có |
| CTX-05 | `context/test_dataflow.py::test_hop_limit_reports_missing`; `pipeline/test_runner.py::test_false_label_is_collapsed_unknown_never` | Một phần |
| CTX-06 | `context/test_dataflow.py::test_size_cap_drops_low_priority_and_records`, `::test_never_raises_on_hops` | Có |
| CTX-07 | `pipeline/test_runner.py::test_context_error_falls_back_to_snippet` | Có |

## LLM (LLM)

| ID | Bằng chứng | Mức |
|---|---|---|
| LLM-01 | `llm/test_engine.py::test_success_one_call` | Có |
| LLM-02 | `pipeline/test_runner.py::test_false_label_is_collapsed_unknown_never`; `bot/test_bot.py::test_render_collapsed_in_details` | Có |
| LLM-03 | `pipeline/test_runner.py::test_false_label_is_collapsed_unknown_never`; `llm/test_redact_prompt_schema.py::test_unknown_without_evidence_ok` | Có |
| LLM-04 | `llm/test_redact_prompt_schema.py::test_validate_rejects`; `llm/test_engine.py::test_bad_json_twice_is_invalid_and_never_more_than_two_calls` | Có |
| LLM-05 | `llm/test_client.py::test_retries_on_429_then_succeeds`; `llm/test_engine.py::test_budget_exhausted_returns_unknown_without_call`, `::test_llm_error_returns_unknown_and_is_not_cached` | Có (timeout chưa có ca riêng) |
| LLM-06 | `llm/test_redact_prompt_schema.py::test_validate_accepts_fenced_and_think` | Có |
| LLM-07 | Không có ca khẳng định chấp nhận khi thiếu `finding_id` | Chưa có |
| LLM-08 | `llm/test_redact_prompt_schema.py::test_validate_rejects` (ca `finding_id="khac"`) | Có |
| LLM-09 | `llm/test_redact_prompt_schema.py::test_validate_rejects_two_json_objects` (mới) | Có |
| LLM-10 | `llm/test_engine.py::test_engines_agree_on_same_input` | Có |

## GitHub App và phản hồi (BOT, FB)

| ID | Bằng chứng | Mức |
|---|---|---|
| BOT-01 | `app/test_flow.py::test_pull_request_gets_one_comment_and_one_neutral_check`; E2E PR #1 | Có |
| BOT-02 | `bot/test_bot.py::test_publisher_posts_once_and_updates`; `bot/test_github_scm.py::test_upsert_creates_then_updates_same_comment` | Có |
| BOT-03 | `app/test_flow.py::test_shadow_mode_posts_nothing_but_stores_results` | Có |
| BOT-04 | `bot/test_bot.py::test_render_collapsed_in_details` | Có |
| BOT-05 | `bot/test_bot.py::test_render_failed_empty_degraded_never_says_safe`; E2E PR #2 | Có |
| BOT-06 | `bot/test_p10.py::test_build_check_is_neutral_data_with_annotations` | Có |
| BOT-07 | `app/test_units.py::test_fetcher_real_local_remote_and_pull_ref_fallback` (kho cục bộ, chưa có fork thật) | Một phần |
| FB-01, FB-02 | `app/test_flow.py::test_fp_reply_by_reviewer_marks_alert_false_author_does_not_when_untrusted`; `bot/test_p10.py::test_resolve_states_trusted_roles` | Có |
| FB-03 | `bot/test_bot.py::test_feedback_parses_fp_tp_per_alert_and_is_idempotent`; E2E PR #1 | Một phần (chưa rõ khẳng định "không tự coi là đã sửa") |
| FB-04 | `bot/test_bot.py::test_feedback_parses_fp_tp_per_alert_and_is_idempotent` | Một phần |
| FB-05 | `pipeline/test_fixdetect.py::test_fixed_when_function_changed_and_marker_gone`; `app/test_flow.py::test_new_commit_marks_previous_alert_fixed` | Có |
| FB-06 | `pipeline/test_fixdetect.py::test_present_when_untouched_and_not_fixed_when_file_deleted` | Một phần (ca "chỉ đổi vị trí" chưa có) |
| FB-07 | `bot/test_github_scm.py::test_reactions_commits_state` | Một phần |

## Bảo mật và vận hành (SEC, OPS)

| ID | Bằng chứng | Mức |
|---|---|---|
| SEC-01 | `app/test_flow.py::test_signature_ping_and_ignored_events`; `app/test_units.py::test_verify_signature_edge_cases` | Có |
| SEC-02 | `app/test_flow.py::test_redelivery_and_same_head_are_not_reprocessed` | Có |
| SEC-03 | `app/test_flow.py::test_oversized_body_rejected`, `::test_repo_allowlist_blocks_other_installations` | Có |
| SEC-04 | `bot/test_p10.py::test_clean_neutralizes_mentions_html_links_and_refs`; `llm/test_redact_prompt_schema.py::test_prompt_injection_stays_inside_data_block` | Có |
| SEC-05 | `llm/test_engine.py::test_redacts_secrets_before_sending`; `scan/test_secrets.py::test_findings_and_bundles_carry_no_secret` | Có |
| SEC-06 | Theo thiết kế (chỉ phân tích tĩnh, `git archive`), không có ca riêng | Chưa có |
| SEC-07 | `app/test_flow.py::test_config_is_read_from_base_branch_only` | Có |
| SEC-08 | `llm/test_redact_prompt_schema.py::test_validate_rejects` (evidence ngoài bundle); LLM không có công cụ (ADR 0003) | Có |
| SEC-09 | Quyền App kiểm tra thủ công khi cài, chưa có hồ sơ | Chưa có |
| OPS-01 | `pipeline/test_runner.py::test_llm_error_degrades_but_keeps_alert` | Có |
| OPS-02 | `pipeline/test_runner.py::test_scan_failure_marks_run_failed`; `bot/test_bot.py::test_render_failed_empty_degraded_never_says_safe` | Có |
| OPS-03 | `app/test_flow.py::test_resume_runs_jobs_left_queued_after_restart` (với GitHub giả) | Có |
| OPS-04 | `pipeline/test_policy_filter.py::test_select_orders_by_severity_and_applies_floor_and_cap`; `app/test_flow.py::test_draft_too_large_and_disabled_check_run` | Có |
| OPS-05 | `app/test_flow.py::test_ops_endpoints_require_admin_token`, `::test_admin_endpoints_hidden_when_no_token_configured` | Có |
| OPS-06 | Không có ca kho không ghi được | Chưa có |
| OPS-07 | `app/test_flow.py::test_redelivery_and_same_head_are_not_reprocessed`; `llm/test_engine.py::test_cache_hit_skips_model` | Một phần (chưa có ca lặp nhiều lần ghi chi phí mỗi lần) |

## Đánh giá (EVAL)

| Nội dung | Bằng chứng | Mức |
|---|---|---|
| Pool, tách tập theo thời gian commit | `evaluation/test_pool_blind_adjudicate.py::test_pool_splits_by_time_and_eval_only_repo_first_occurrence_wins`, `::test_build_pool_splits_by_commit_time` | Có |
| Phiếu mù, không đọc output mô hình | `::test_sheets_are_blind_and_shuffled`, `::test_labeling_module_never_reads_model_output` | Có |
| Một người gán + kiểm định mẫu | `::test_single_labeler_export_only_when_requested`, `::test_audit_sample_size_and_strata`, `::test_audit_sheet_hides_primary_labels`, `::test_kappa_on_audit_overlap`; `evaluation/test_cli_eval.py::test_cli_single_labeler_then_audit_sample` | Có |
| Kappa, phân xử, cổng kappa | `::test_kappa_queue_finalize_and_gate`, `::test_low_kappa_blocks_finalize` | Có |
| Khóa manifest | `evaluation/test_compute_freeze_export.py::test_freeze_blocks_changes`; `evaluation/test_cli_eval.py::test_full_flow_with_freeze_gate` | Có |
| Số đo, Wilson, McNemar, kappa, bootstrap | `evaluation/test_metrics.py` (5 ca); `::test_report_numbers` | Có |
| Nối B/C từ lượt chạy sau | `pipeline/test_semgrep_e2e.py::test_bc_verdicts_join_pool_after_scan_only` | Có |
| Xuất số liệu không lộ định danh | `::test_export_suppresses_small_cells_and_has_no_identifiers` | Có |

## Tổng hợp

- **Chưa có:** CTX-04, LLM-07, SEC-06, SEC-09, OPS-06.
- **Một phần:** SCN-07, NRM-02, CTX-02, CTX-05, BOT-07, FB-03, FB-04, FB-06, FB-07, OPS-07.
- Trong nhóm P0 (scanner SQL/secret, base/head, comment/check, lỗi LLM/scanner, che secret, `fp`/`tp`), các ca thiếu hoặc một phần là SCN-07, NRM-02, LLM-07, FB-03, FB-04. Cần bổ sung trước cổng 5.7 của thiết kế.

## Live LLM test

`PR_TRIAGE_LLM_*` được nạp từ `.env` vào môi trường của lệnh (không in giá trị), chạy `uv run pytest tests/llm/test_live.py`: **2 failed**, nhà cung cấp trả HTTP 401 "API key expired". Đây là lỗi cấu hình khóa, không phải lỗi mã: client báo lỗi đúng và không lộ khóa. Cần người dùng cấp khóa mới rồi chạy lại.

**Chạy lại sau khi người dùng cấp khóa mới (2026-11-18):** `uv run pytest tests/llm/test_live.py` → **2 passed** (PlainTriageEngine và TriageEngine trả nhận định hợp lệ, có token).
