"""Lấy mã của PR bằng `git fetch` theo SHA, chỉ đọc (ADR 0012 D3), token không vào argv."""

from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from pr_triage.core.errors import ScmError
from pr_triage.core.scm import GitRemote


class GitFetcher:
    def __init__(
        self, url_template: str = "https://github.com/{repo}.git", timeout_s: int = 300
    ) -> None:
        self._template = url_template
        self._timeout = timeout_s

    @staticmethod
    def _env(
        token: str, url: str, username: str = "x-access-token", bearer: bool = False
    ) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        if url.startswith("http") and token:
            if bearer:
                header = f"Authorization: Bearer {token}"
            else:
                basic = base64.b64encode(f"{username}:{token}".encode()).decode()
                header = f"Authorization: Basic {basic}"
            env.update(
                GIT_CONFIG_COUNT="1",
                GIT_CONFIG_KEY_0="http.extraheader",
                GIT_CONFIG_VALUE_0=header,
            )
        return env

    def _git(self, cwd: Path, env: dict[str, str], token: str, *args: str) -> bool:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, env=env, capture_output=True, text=True,
            timeout=self._timeout, check=False,
        )  # fmt: skip
        if proc.returncode != 0:
            err = proc.stderr.replace(token, "***") if token else proc.stderr
            self.last_error = err[-300:]
        return proc.returncode == 0

    last_error = ""

    @contextmanager
    def checkout(
        self,
        repo: str,
        token: str,
        shas: Sequence[str],
        pr_number: int,
        optional_shas: Sequence[str] = (),
        remote: GitRemote | None = None,
    ) -> Iterator[Path]:
        """Cấp một kho git tạm chứa các commit cần thiết. `optional_shas` lỗi thì bỏ qua.

        `remote` (từ nhà cung cấp SCM) quyết định địa chỉ, cách xác thực và ref dự phòng của PR;
        không có thì dùng mẫu địa chỉ GitHub như trước.
        """
        url = remote.url if remote else self._template.format(repo=repo)
        env = (
            self._env(token, url, remote.username, remote.bearer)
            if remote
            else self._env(token, url)
        )
        pr_refs = remote.pr_refs(pr_number) if remote else [f"refs/pull/{pr_number}/head"]
        with tempfile.TemporaryDirectory(prefix="pr-triage-fetch-") as tmp:
            path = Path(tmp) / "repo"
            path.mkdir()

            def run(*a: str) -> bool:
                return self._git(path, env, token, *a)

            run("init", "-q")
            run("remote", "add", "origin", url)
            for i, sha in enumerate(shas):
                ok = run("fetch", "-q", "--depth=1", "--no-tags", "origin", sha)
                if not ok and i == len(shas) - 1:
                    for ref in pr_refs:
                        ok = run("fetch", "-q", "--depth=1", "--no-tags", "origin", ref)
                        if ok:
                            break
                if not ok or not run("cat-file", "-e", f"{sha}^{{commit}}"):
                    raise ScmError(f"không lấy được commit {sha[:8]} của {repo}: {self.last_error}")
            for sha in optional_shas:
                run("fetch", "-q", "--depth=1", "--no-tags", "origin", sha)
            yield path

    def sync(
        self, path: Path, remote: GitRemote, token: str, pr_number: int, base_ref: str = ""
    ) -> str:
        """Cập nhật kho cục bộ bền (Jenkins): `origin/base` là nhánh đích, `origin/pr` là đầu PR.

        Trả về tên nhánh đích đã dùng (mặc định của repo nếu `base_ref` trống).
        """
        path.mkdir(parents=True, exist_ok=True)
        env = self._env(token, remote.url, remote.username, remote.bearer)

        def run(*a: str) -> bool:
            return self._git(path, env, token, *a)

        if not (path / ".git").exists():
            run("init", "-q")
        if not run("remote", "set-url", "origin", remote.url):
            run("remote", "add", "origin", remote.url)
        base = base_ref
        if not base:
            proc = subprocess.run(
                ["git", "ls-remote", "--symref", "origin", "HEAD"], cwd=path, env=env,
                capture_output=True, text=True, timeout=self._timeout, check=False,
            )  # fmt: skip
            for line in proc.stdout.splitlines():
                if line.startswith("ref:"):
                    base = line.split()[1].removeprefix("refs/heads/")
                    break
        if not base:
            raise ScmError("không xác định được nhánh đích của repo")
        if not run(
            "fetch",
            "--no-tags",
            "--force",
            "origin",
            f"+refs/heads/{base}:refs/remotes/origin/base",
        ):
            raise ScmError(f"không lấy được nhánh đích {base}: {self.last_error}")
        for ref in remote.pr_refs(pr_number):
            if run("fetch", "--no-tags", "--force", "origin", f"+{ref}:refs/remotes/origin/pr"):
                return base
        raise ScmError(f"không lấy được đầu PR {pr_number}: {self.last_error}")
