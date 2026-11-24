# Quy trình Git và release

## Mô hình nhánh

```
{dev}/{slug}/{nội dung}  ──PR──▶  dev  ──PR──▶  main  ──tag vX.Y.Z──▶  release
```

| Nhánh | Vai trò | Ai ghi vào |
|---|---|---|
| `main` | Release candidate. Luôn ở trạng thái chạy được | Chỉ merge từ `dev` bằng PR |
| `dev` | Bản phát triển chung của nhóm | Chỉ merge từ nhánh cá nhân bằng PR |
| `{dev}/{slug}/{nội dung}` | Nhánh làm việc cá nhân | Chủ nhánh |

**Đặt tên nhánh cá nhân:** `{tên dev}/{slug}/{nội dung ngắn gọn}`, chữ thường, nối bằng dấu gạch ngang.

- `{tên dev}`: tên GitHub hoặc tên ngắn của bạn, ví dụ `trinq`.
- `{slug}`: mảng việc, ví dụ `context`, `bot`, `llm`, `labeling`, `docs`, `ci`, `setup`.
- `{nội dung}`: việc cụ thể, ví dụ `taint-extractor`.

Ví dụ: `trinq/context/taint-extractor`, `kien/bot/pr-comment`, `quangha/pipeline/dedup`. Viết không dấu.

Các nhánh cũ như `son-dev`, `kien-dev` vẫn còn trên remote. Đổi sang quy ước mới khi mở nhánh tiếp theo, không cần đổi tên nhánh cũ.

## Làm việc hằng ngày

```bash
git switch dev && git pull
git switch -c trinq/context/taint-extractor
# ... làm việc, commit nhỏ theo Conventional Commits ...
make check                      # lint + test trước khi mở PR
git push -u origin trinq/context/taint-extractor
gh pr create --base dev
```

- PR vào `dev`: ít nhất 1 người review, CI xanh, squash hoặc rebase merge cho gọn lịch sử.
- Kéo `dev` mới về nhánh cá nhân bằng rebase: `git fetch && git rebase origin/dev`. Chỉ force-push nhánh cá nhân, dùng `--force-with-lease`.
- Không bao giờ push thẳng `main` hay `dev`, không `--no-verify`.
- Xóa nhánh cá nhân sau khi merge.

## Commit

Dạng `type(scope): mô tả`. `type`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`. Mô tả tiếng Việt, ngắn, nói *vì sao* khi không hiển nhiên.

## Release

`main` nhận code từ `dev` qua PR (merge commit). Release dùng `bump-my-version`, cấu hình trong `pyproject.toml` (`[tool.bumpversion]`). Lệnh này sửa phiên bản, commit và tạo tag trong một bước.

```bash
git switch main && git pull
make bump PART=patch      # hoặc minor, major  -> commit "chore(release): ..." + tag vX.Y.Z
git push origin main --follow-tags
```

Khi tag `v*.*.*` được đẩy lên, workflow `release.yml` kiểm tra tag khớp phiên bản trong `pyproject.toml` rồi tạo GitHub Release với ghi chú tự sinh. Sau release, merge ngược `main` vào `dev` để `dev` có commit bump.

Chọn `PART`: `patch` cho sửa lỗi và chỉnh tài liệu, `minor` cho một mốc nội dung mới (ví dụ xong một RQ), `major` cho mốc nộp bài.

## Tag khóa cấu hình đánh giá

Proposal (mục 7.3) yêu cầu prompt, cấu hình, ngưỡng và kế hoạch phân tích được gắn tag trước khi chạy tập `eval`. Dùng tag có dạng `eval-freeze-<n>` (ví dụ `eval-freeze-1`) đặt trên commit của `dev`. Tag không bao giờ bị xóa hay di chuyển. Cần cấu hình mới thì tạo tag mới.

## Thiết lập một lần cho mỗi bản clone

```bash
make setup           # tạo môi trường uv, cài công cụ dev
uv run pre-commit install
```

Quản trị viên repo bật branch protection cho `main` và `dev`: bắt buộc PR, ít nhất 1 review, CI xanh, cấm force-push.
