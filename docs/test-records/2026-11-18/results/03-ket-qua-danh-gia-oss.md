# Kết quả đánh giá A/B/C trên mã Java mã nguồn mở — 2026-11-18

> Bản lưu trong repo. Tài liệu gốc và các tài liệu được nhắc tới (proposal, ADR 0015–0017, runbook) nằm trong hồ sơ `.docs/` của nhóm, ngoài repo.

Kịch bản: `docs/test-records/2026-11-18/scenarios/03-kich-ban-danh-gia-oss.md`.

> **Đính chính (bản 2, cùng ngày):** bản đầu báo B 64%, C 66% FP-removal trên `eval`. 31 nhận định ở mốc DSpace `462ed443` là `unknown` giả do hết trần 200.000 token mỗi lượt chạy (không gọi LLM). Sau khi thêm `--budget-pr-tokens` và chạy lại mốc đó, số đúng là **B 74%, C 74%**. TP-loss không đổi. Chi tiết ở mục 5 và runbook.

| | |
|---|---|
| Phạm vi | 6 repo Java mã nguồn mở, quét 21 mốc lịch sử mỗi repo (ADR 0015, 0016). **Không phải dữ liệu công ty Z, không phải cảnh báo trên PR.** |
| Cấu hình | Tag `eval-freeze-1` (commit `6b17db9`), manifest `8b941c3b…`: Semgrep CE 1.185.0, 3 luật tùy chỉnh + 29 luật registry (CWE-89/78/79/22/90/643); B bán kính 40; hiển thị C; model `deepseek/deepseek-v4.1-flash-1017`, prompt `v1`. Trần token mỗi lượt chạy 3.000.000 (tham số vận hành) |
| Tách tập | Theo repo. `dev`: OFBiz, OpenCms, JSPWiki (84). `eval`: DSpace, OpenMRS Core, Roller (121 sau gộp trùng) |
| Nhãn `eval` | Nhãn tham chiếu của **hai người gán AI**: Claude Opus gán toàn bộ (đọc sơ lược), Claude Sonnet độc lập gán 50 ca mẫu; ca bất đồng → Không xác định (ADR 0017). **Không có kiểm định bằng người** |
| Nhãn D2 | Đáp án của OWASP BenchmarkJava 1.2 (không do AI gán) |

## 1. Kết quả chính — tập `eval` (mã thật)

121 cảnh báo duy nhất: 13 Thật, 99 Sai, 9 Không xác định. Wilson 95%.

| | A | B (LLM + ±40 dòng) | C (LLM + luồng dữ liệu) |
|---|---|---|---|
| FP-removal | 0/99 | **73/99 = 74%** [64–81%] | **73/99 = 74%** [64–81%] |
| TP-loss | 0/13 | **0/13** [0–23%] | **0/13** [0–23%] |
| `unknown` | — | 25/112 = 22% | 18/112 = 16% |
| `invalid` | — | 2/112 = 2% | 11/112 = 10% |
| Đúng so với nhãn | 13/112 | 81/112 = 72% | 82/112 = 73% |
| Bootstrap theo lượt chạy, FP-removal | — | 61–88% | 67–85% |

- **RQ1 — tỉ lệ cảnh báo sai nền:** 99/112 = **88%** [81–93%]; biên `undetermined`: 82% (nếu đều Thật) đến 89% (nếu đều Sai).
- **B so với C (McNemar):** chỉ B đúng 9, chỉ C đúng 10, p = 1,0. **Không khác biệt.**
- **Lượt đọc tiết kiệm trên mỗi lỗi thật bị mất:** không xác định (không lỗi thật nào bị thu gọn).
- **Độ nhạy, 44 ca có nhãn người gán thứ hai** (3 Thật, 34 Sai, 7 KXĐ): B 26/34 = 76%, C 24/34 = 71%; TP-loss 0/3; McNemar p = 0,69. Cùng chiều.

## 2. Kiểm chéo có đáp án — D2 (OWASP BenchmarkJava)

147 test case (25 mỗi CWE, CWE-643 có 22), không trùng 30 ca hiệu chuẩn; chỉ chấm cảnh báo có CWE trùng loại lỗi của test case (163 chấm, 24 bị loại vì lệch loại).

| | B | C |
|---|---|---|
| FP-removal | 51/74 = 69% [58–78%] | **68/74 = 92%** [83–96%] |
| TP-loss | 1/89 = 1% [0–6%] | 3/89 = 3% [1–9%] |
| `unknown` | 29/163 = 18% | 4/163 = 2% |
| Đúng | 122/163 = 75% | **152/163 = 93%** |
| Lượt đọc tiết kiệm / lỗi thật bị mất (theo tỉ lệ nền 45% của mẫu) | 51 | 23 |

- Tỉ lệ cảnh báo sai nền của mẫu: 74/163 = 45%.
- McNemar: chỉ B đúng 8, chỉ C đúng 38, **p ≈ 9e-06 — C tốt hơn rõ rệt.**
- Ngoại suy lượt đọc tiết kiệm / lỗi thật bị mất theo tỉ lệ nền: 22% → B 17, C 7,7; 76% → B 194, C 86; 92% → B 705, C 314. Ví dụ ở proposal mục 2 cho thấy giá trị phụ thuộc mạnh vào tỉ lệ nền; ở đây C loại nhiều hơn nhưng cũng mất nhiều lỗi thật hơn nên tỉ số thấp hơn B.

**So D2 với `eval`:** C vượt B rất xa trên BenchmarkJava (test case được thiết kế với luồng dữ liệu qua hàm phụ, điều kiện hằng, collection) nhưng **không vượt trên mã thật**. Hai giải thích chưa tách được: (1) mã thật trong mẫu ít dạng "qua hàm phụ" mà bộ trích C xử lý tốt; (2) mô hình có thể đã thấy BenchmarkJava khi huấn luyện. Chưa chạy câu thăm dò "đây là test case nào".

## 3. Đồng thuận nhãn, độ ổn định, tất định

- Kappa (Opus, Sonnet) trên 50 ca `eval`: **0,613**. Đồng ý tuyệt đối ở 40 ca Sai; bất đồng ở ca Thật.
- Hiệu chuẩn Opus trên 30 ca BenchmarkJava (B4): 29/30, kappa 0,933.
- **Độ ổn định** (3 tiến trình độc lập, không cache, 90 cảnh báo `eval` ở 3 mốc đầu): cảnh báo đổi nhãn qua 3 lần — **B 11/90 = 12%, C 20/90 = 22%**. Dao động chủ yếu giữa `unknown` và một nhãn chắc chắn; C dao động nhiều hơn.
- **Tất định của quét/gộp trùng:** ba lần chạy lại cho đúng tập 90 `finding_id` như lượt quét gốc (3/3).

## 4. Đọc theo giả thuyết (thiết kế mục 6.9)

| Giả thuyết | `eval` | D2 | Kết luận |
|---|---|---|---|
| H1: FP nền < 76% | 88% [81–93%] | 45% (mẫu chọn theo cách khác, không dùng cho H1) | **Không ủng hộ** trên mã thật |
| H2a: C mất ít lỗi thật hơn B | 0/13 so với 0/13 | 3/89 so với 1/89 | **Mẫu quá nhỏ trên `eval`**; trên D2 C mất nhiều hơn (không có ý nghĩa thống kê) |
| H2b: C không kém B quá 10 điểm FP-removal | 74% so với 74% | 92% so với 69% | **Ủng hộ** |
| H2c: tại chỗ so với cloud | — | — | Không làm |
| "Đáng dùng" (proposal 7.9) | FP-removal 74% ≥ 50% đạt; TP-loss 0% nhưng cận trên 23%; thời gian/chi phí trên PR chưa đo | | **Chưa đủ bằng chứng** |

## 5. Phát hiện về mã và dữ liệu trong đợt này

| Phát hiện | Mức | Xử lý |
|---|---|---|
| Manifest `freeze` không băm bán kính, cách hiển thị, luật ngoài repo | major | Sửa trước khi khóa (`2fed98e`), có test |
| Đầu ra LLM có hai JSON object được nhận (LLM-09) | major | Từ chối (`bb1b6ec`), có test |
| Test bị `.env` cục bộ ảnh hưởng | minor | `PR_TRIAGE_NO_DOTENV` (`bb1b6ec`) |
| Pool lấy cả bản trùng giữa các luật đã bị pipeline gộp (22/143 mục `eval` không có nhận định) | major | Sửa `build_pool` (`0812e89`), có test; pool dựng lại trùng khớp bản loại trùng tay; TD-3 đã đóng |
| Trần token 200.000 mỗi lượt chạy cố định trong mã làm 31 nhận định `eval` và 287 nhận định D2 thành `unknown` giả | major | Thêm `--budget-pr-tokens` (`f4204a6`), có test; chạy lại phần bị ảnh hưởng |
| Đầu ra bị cắt cụt (`finish_reason=length`) | minor | 15 nhận định `eval`, 12 ở D2 → `invalid`/`unknown`; cảnh báo giữ nguyên theo thiết kế. Chưa sửa (cần tăng `max_tokens` của client hoặc rút gọn ngữ cảnh) |
| Luật `java-sql-concat-flow` bắt nhầm `execute()` không phải SQL | (RQ1) | Ghi là chất lượng bộ luật, không phải lỗi LLM |

## 6. Chi phí và thời gian

- B8 (`eval`, 19 lượt + 1 lượt chạy lại): 122 cảnh báo × (B + C); khoảng 4.300 token vào và 1.800 token ra mỗi cảnh báo cho cả hai cách. Lượt chạy lại mốc DSpace (52 cảnh báo): 259 s.
- D2: một lượt 187 cảnh báo, 865 s.
- Chưa quy ra tiền (chưa chốt bảng giá); thời gian là của lượt quét mốc lịch sử, không phải thời gian phản hồi trên PR.

## 7. Giới hạn

1. Không phải doanh nghiệp, không phải PR; không đo RQ3 (hành vi lập trình viên) hay độ trễ trên PR.
2. Nhãn `eval` do hai mô hình AI cùng họ gán, đọc sơ lược; kappa 0,613 đo nhất quán, không đo độ đúng. Người gán thứ hai đọc rất nhanh (51 s cho 50 ca).
3. Chỉ 13 lỗi thật trên `eval`; khoảng tin cậy TP-loss 0–23%.
4. Mô hình có thể đã thấy mã nguồn mở này và BenchmarkJava khi huấn luyện; chưa chạy câu thăm dò.
5. `eval` còn 121 < 140 (mức tối thiểu) sau gộp trùng; báo đúng cỡ mẫu thực tế.
6. 31 nhận định `eval` được lấy lại sau khi đã xem kết quả bản đầu. Thay đổi chỉ là gỡ trần token (không đổi prompt, model, bán kính, luật); 21 cảnh báo khác cùng mốc được lấy mẫu lại với cùng cấu hình. Độ dao động đo ở mục 3 là thước đo cho mức ảnh hưởng của việc lấy mẫu lại.
7. Chưa làm: D3 Vul4J (RQ4), Jenkins J1–J6, mốc RQ3 lịch sử (`replay --side first`). D4 xong ở mục 9.

## 8. Kết luận ngắn

Trên 121 cảnh báo của ba repo Java mã nguồn mở, LLM thu gọn được khoảng **ba phần tư cảnh báo sai** (B và C đều 74%) mà **không thu gọn lỗi thật nào trong 13 lỗi thật**. Trên mã thật, ngữ cảnh luồng dữ liệu (C) **không tốt hơn** cửa sổ mã rộng (B); trên BenchmarkJava có đáp án, C tốt hơn rất rõ (92% so với 69%) nhưng mất nhiều lỗi thật hơn một chút. Nhận định dao động 12–22% giữa các lần chạy. Tỉ lệ cảnh báo sai nền của bộ luật trên mã thật là 88%. Chưa đủ bằng chứng để kết luận "đáng dùng" theo đủ bốn tiêu chí của proposal.

## 9. D4 — GitHub App trên PR thật của fork (bổ sung 2026-11-19)

Fork `vudinhminh08/roller` (công khai), App PR Triage hiện có, cấu hình đã khóa (hiển thị C, B bán kính 40 qua `PR_TRIAGE_SNIPPET_RADIUS`, cả hai bộ luật, trần token 3.000.000). 6 PR do nhóm tạo trên nhánh `master` của fork; đóng, không merge, đã xóa nhánh.

| PR | Thay đổi | Cảnh báo mới | B | C | Token | Mở → xong |
|---|---|---|---|---|---|---|
| #1 | Bỏ `escapeXml10` ở `TagDataServlet` (đảo ngược bản sửa 2021) | 3 | 1 Thật, 2 unknown | 1 Sai, 1 unknown, 1 invalid | 43.156 | 62 s |
| #2 | Bỏ `escapeHTML` ở `CommentDataServlet` | 0 (bộ quét bỏ sót: dòng báo cũ trùng dấu vân tay ở base) | — | — | 0 | 32 s |
| #3 | Thêm truy vấn JDBC ghép tham số request | 2 | 2 Thật | 2 Thật | 13.902 | 69 s |
| #4 | Thêm đọc file theo tham số request | 2 | 2 Thật | 2 Thật | 8.052 | 80 s |
| #5 | Thêm truy vấn `PreparedStatement` (đối chứng âm) | 0 | — | — | 0 | 85 s |
| #6 | Chỉ sửa tài liệu | 0 | — | — | 0 | 94 s |

- **Độ trễ từ mở/mở lại PR tới khi lượt chạy xong: trung vị 80 s, tối đa 94 s** (hàng đợi xử lý tuần tự nên PR sau chờ PR trước). Đạt tiêu chí ≤ 15 phút cho repo cỡ Roller. Tổng 65.110 token cho 6 PR.
- Hai lỗi thật cố ý (#3, #4) được cả B và C giữ (Thật); không cảnh báo thừa ở #5, #6.
- **Hạn chế:** chỉ 6 PR do nhóm tạo, không có người review thật → mô tả, không phải bằng chứng hành vi lập trình viên (RQ3). Độ trễ đo bằng thời điểm mở lại PR và thời điểm lượt chạy kết thúc trong DB; chưa tính thời gian đăng comment.
- Sự cố trong lúc chạy: `.pr-triage.yml` viết sai khóa `secrets` (bot báo "cấu hình sai", đúng thiết kế); Quick Tunnel hết hạn qua đêm → mở tunnel mới, cập nhật webhook URL qua API `PATCH /app/hook/config` bằng JWT của App. Sửa mã cho App đọc bán kính và trần token (`121fa04`); TD-4 (trần token của App cộng dồn giữa các PR) còn mở.

---

# Phụ lục: đối chiếu theo kịch bản

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
