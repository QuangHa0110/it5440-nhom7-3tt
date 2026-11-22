"""Đường Jenkins: tham số job, hỏi định kỳ PR đang mở (ADR 0018, thay `ci_helper.py` của P13)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from pathlib import Path

from pr_triage.core.delivery import Channel, RepoGate, ScanRequest
from pr_triage.core.errors import ScmError
from pr_triage.core.scm import OpenPr, split_repo
from pr_triage.triggers.base import Trigger, TriggerError

# GitHub: owner/repo. Loại khác có tiền tố và có thể lồng nhóm: gitlab:nhom/con/du-an (ADR 0021).
REPO_RE = re.compile(r"^(?:[a-z]+:)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
REF_RE = re.compile(r"^[A-Za-z0-9_./-]*$")


class JenkinsParamsTrigger(Trigger[Mapping[str, str]]):
    """Tham số của job `pr-triage`: REPO, PR, BASE_REF (tuỳ chọn), HEAD_SHA (tuỳ chọn)."""

    @property
    def channel(self) -> Channel:
        return Channel.JENKINS

    def parse(self, source: Mapping[str, str]) -> list[ScanRequest]:
        repo = source.get("REPO", "").strip()
        pr = source.get("PR", "").strip()
        base_ref = source.get("BASE_REF", "").strip()
        sha = source.get("HEAD_SHA", "").strip()
        if not REPO_RE.match(repo):
            raise TriggerError(f"REPO không hợp lệ: {repo!r}")
        try:
            split_repo(repo)
        except ScmError as exc:
            raise TriggerError(f"REPO không hợp lệ: {exc}") from exc
        if not pr.isdigit() or int(pr) <= 0:
            raise TriggerError(f"PR không hợp lệ: {pr!r}")
        if sha and not SHA_RE.match(sha):
            raise TriggerError(f"HEAD_SHA không hợp lệ: {sha!r}")
        if not REF_RE.match(base_ref) or ".." in base_ref or base_ref.startswith("-"):
            raise TriggerError(f"BASE_REF không hợp lệ: {base_ref!r}")
        return [ScanRequest(repo, int(pr), sha, self.channel, base_ref)]


class PollState:
    """Trạng thái "đã thấy đầu nhánh nào" của từng PR, lưu bằng một file JSON."""

    def __init__(self, seen: Mapping[str, str] | None = None) -> None:
        self._seen: dict[str, str] = dict(seen or {})

    @classmethod
    def load(cls, path: Path) -> PollState:
        if not path.exists():
            return cls()
        return cls(json.loads(path.read_text("utf-8")))

    def has_seen(self, repo: str, pr_number: int, sha: str) -> bool:
        return self._seen.get(f"{repo}#{pr_number}") == sha

    def advance(self, prs_by_repo: Mapping[str, list[OpenPr]], failed: frozenset[str]) -> PollState:
        """Trạng thái mới: PR đã đóng rơi ra; repo hỏi lỗi giữ nguyên trạng thái cũ."""
        nxt = {k: v for k, v in self._seen.items() if k.split("#", 1)[0] in failed}
        for repo, prs in prs_by_repo.items():
            for pr in prs:
                if not pr.draft:
                    nxt[f"{repo}#{pr.number}"] = pr.head_sha
        return PollState(nxt)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self._seen, indent=1, sort_keys=True), "utf-8")

    def as_dict(self) -> dict[str, str]:
        return dict(self._seen)


class PollTrigger(Trigger[Mapping[str, list[OpenPr]]]):
    """Chọn PR có đầu nhánh khác lần hỏi trước. PR nháp bị bỏ qua."""

    def __init__(self, state: PollState) -> None:
        self._state = state

    @property
    def channel(self) -> Channel:
        return Channel.JENKINS

    def parse(self, source: Mapping[str, list[OpenPr]]) -> list[ScanRequest]:
        out: list[ScanRequest] = []
        for repo, prs in source.items():
            for pr in prs:
                if pr.draft or self._state.has_seen(repo, pr.number, pr.head_sha):
                    continue
                out.append(ScanRequest(repo, pr.number, pr.head_sha, self.channel, pr.base_ref))
        return out


class PollOutcome:
    def __init__(
        self, requests: list[ScanRequest], asked: int, failed: frozenset[str], next_state: PollState
    ) -> None:
        self.requests = requests
        self.asked = asked
        self.failed = failed
        self.next_state = next_state


class JenkinsPoller:
    """Hỏi GitHub về các repo tên đầy đủ trong danh sách cho phép, rồi chọn PR cần quét."""

    def __init__(self, lister: Callable[[str], list[OpenPr]], gate: RepoGate) -> None:
        self._lister = lister
        self._gate = gate
        self.errors: list[str] = []

    def poll(self, state: PollState) -> PollOutcome:
        prs_by_repo: dict[str, list[OpenPr]] = {}
        failed: set[str] = set()
        for repo in self._gate.allow.exact_names():
            if not REPO_RE.match(repo) or not self._gate.admits(Channel.JENKINS, repo):
                continue
            try:
                prs_by_repo[repo] = self._lister(repo)
            except Exception as exc:  # noqa: BLE001 - một repo lỗi không làm hỏng cả vòng
                code = getattr(exc, "code", None) or type(exc).__name__
                failed.add(repo)
                self.errors.append(f"{repo}: không hỏi được GitHub ({code})")
        requests = PollTrigger(state).collect(prs_by_repo, self._gate)
        nxt = state.advance(prs_by_repo, frozenset(failed))
        return PollOutcome(requests, len(prs_by_repo), frozenset(failed), nxt)
