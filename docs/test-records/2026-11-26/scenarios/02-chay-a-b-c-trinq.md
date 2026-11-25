# Kịch bản 02 — Chạy A, B, C trên 19 PR đã chốt (trinq)

**Mục tiêu:** có nhận định B và C trên cùng tập cảnh báo của A, theo bước 5 của hướng dẫn.

**Tiền điều kiện:** danh sách trong [bảng đăng ký](../results/dang-ky-pr-trinq.md); khóa LLM trong `.env` (không commit).

**Cách làm:** với mỗi PR:

```bash
uv run pr-triage run --repo data/raw/<ma-repo> --repo-alias <ma-repo> --base <sha-base> --head <sha-head> --pr=<so> \
  --variants B,C --no-secrets --snippet-radius 40 --display C \
  --db data/team/store.sqlite --out data/raw/<ma-repo>-run/<sha>
```

**Kết quả mong đợi:** mọi lượt `ok`, mỗi cảnh báo có một nhận định B và một nhận định C.

**Kết quả thực tế:** đạt, 19/19 lượt `ok`, không nhận định nào lỗi. Xem [ket-qua-abc-trinq.md](../results/ket-qua-abc-trinq.md). Không đăng comment lên repo gốc.
