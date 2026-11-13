"""Tạo GitHub App từ manifest, không phải bấm từng ô trên giao diện.

Bước 1: `python scripts/github_app_manifest.py html --webhook-url https://HOST/webhook --name "PR Triage x"`
        ghi ra app-manifest.html. Mở tệp trong trình duyệt đã đăng nhập GitHub, bấm nút, xác nhận.
Bước 2: GitHub chuyển về http://localhost:3000/?code=XXXX (trang trống là bình thường). Chép giá trị code.
Bước 3: `python scripts/github_app_manifest.py exchange XXXX --out secrets/` đổi code lấy ID, khóa riêng
        và secret webhook, ghi vào secrets/<tên>.env và .pem (quyền 0600, không in ra màn hình).
"""

import argparse
import html
import json
import stat
from pathlib import Path
from urllib.request import Request, urlopen

MANIFEST = Path(__file__).resolve().parents[1] / "deploy" / "github-app-manifest.json"


def build_manifest(webhook_url: str, name: str, homepage: str, redirect: str) -> dict[str, object]:
    m = json.loads(MANIFEST.read_text("utf-8"))
    m["name"] = name
    m["url"] = homepage
    m["hook_attributes"]["url"] = webhook_url
    m["redirect_url"] = redirect
    return m  # type: ignore[no-any-return]


def page(manifest: dict[str, object], org: str | None) -> str:
    target = (
        f"https://github.com/organizations/{org}/settings/apps/new"
        if org
        else "https://github.com/settings/apps/new"
    )
    data = html.escape(json.dumps(manifest), quote=True)
    return (
        "<!doctype html><meta charset='utf-8'><title>Tạo GitHub App</title>"
        f"<form action='{target}' method='post'>"
        f"<input type='hidden' name='manifest' value=\"{data}\">"
        "<button type='submit' style='font-size:18px;padding:12px 20px'>Tạo GitHub App trên GitHub</button>"
        "</form>"
    )


def exchange(code: str, out: Path) -> dict[str, str]:
    req = Request(
        f"https://api.github.com/app-manifests/{code}/conversions",
        method="POST",
        headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        data=b"",
    )
    with urlopen(req, timeout=30) as resp:  # noqa: S310 - URL cố định tới api.github.com
        data = json.loads(resp.read())
    out.mkdir(parents=True, exist_ok=True)
    pem = out / f"{data['slug']}.private-key.pem"
    pem.write_text(data["pem"], "utf-8")
    pem.chmod(stat.S_IRUSR | stat.S_IWUSR)
    env = out / f"{data['slug']}.env"
    env.write_text(
        f"GITHUB_APP_ID={data['id']}\nGITHUB_APP_PRIVATE_KEY_PATH={pem}\n"
        f"GITHUB_WEBHOOK_SECRET={data['webhook_secret']}\n",
        "utf-8",
    )
    env.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return {
        "app_id": str(data["id"]),
        "slug": str(data["slug"]),
        "html_url": str(data["html_url"]),
        "env_file": str(env),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("html")
    h.add_argument("--webhook-url", required=True)
    h.add_argument("--name", required=True)
    h.add_argument("--homepage", default="https://github.com")
    h.add_argument("--redirect", default="http://localhost:3000/")
    h.add_argument("--org", help="tạo trong một tổ chức thay vì tài khoản cá nhân")
    h.add_argument("--out", type=Path, default=Path("app-manifest.html"))
    e = sub.add_parser("exchange")
    e.add_argument("code")
    e.add_argument("--out", type=Path, default=Path("secrets"))
    args = ap.parse_args(argv)
    if args.cmd == "html":
        m = build_manifest(args.webhook_url, args.name, args.homepage, args.redirect)
        args.out.write_text(page(m, args.org), "utf-8")
        print(f"đã ghi {args.out}. Mở bằng trình duyệt và bấm nút.")
        return 0
    result = exchange(args.code, args.out)
    for k, v in result.items():
        print(f"{k}: {v}")
    print(
        "Khóa riêng và secret webhook nằm trong tệp env trên, không in ra màn hình. Không commit."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
