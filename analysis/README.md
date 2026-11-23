# analysis

Mã phân tích và thí nghiệm bổ sung cho bài báo. Không sửa `src/`; chỉ dùng `pr_triage` như thư viện.

## seeded_bugs.py

Bộ lỗi gieo có kiểm soát cho CWE-89 (Java). Nhãn đáp án quyết định lúc sinh mã, không do người hay AI gán.
11 mẫu luồng dữ liệu, mỗi mẫu có một ca `vuln` (lỗi thật) và một ca `safe` (đối chứng).

```bash
uv run python -m analysis.seeded_bugs generate --out data/seeded --seed 0 --per-cell 5
uv run python -m analysis.seeded_bugs scan --corpus data/seeded --out data/seeded/results.csv
```

- `generate` ghi `data/seeded/manifest.json` và repo git `data/seeded/corpus/` (một commit). Từ chối ghi đè corpus đã có, dùng `--force` để sinh lại.
- `scan` chạy Semgrep với `configs/semgrep/java-injection.yml` và thử bộ trích ngữ cảnh C tại dòng sink thật
  của mọi ca, nên độ phủ của bộ trích C đo được riêng, không phụ thuộc công cụ quét có báo hay không.
- Chạy các cách A, B, C trên corpus bằng pipeline hiện có (B và C cần khóa LLM trong `.env`):

```bash
uv run pr-triage run --repo data/seeded/corpus --repo-alias seeded --base none --head HEAD --pr 1 \
  --rules configs/semgrep/java-injection.yml --no-secrets --db data/seeded/store.sqlite --out data/seeded/out
```

Đây là bộ tổng hợp: đo được độ phủ và độ chính xác theo dạng luồng, không thay thế dữ liệu mã thật.
Các ca trong cùng mẫu chỉ khác tên định danh, nên đơn vị độc lập là mẫu (11), không phải ca (110). Báo cáo theo từng mẫu,
không gộp mọi ca để tính khoảng tin cậy.
Hai test `xfail(strict=True)` ghi lại hai khoảng trống đã biết của bộ trích C (`append` và trường đối tượng);
khi sửa bộ trích, test sẽ báo để gỡ `xfail`.
