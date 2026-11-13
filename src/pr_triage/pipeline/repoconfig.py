"""`.pr-triage.yml`: cấu hình theo repo, đọc từ nhánh đích (ADR 0012 D5), kiểm tra chặt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

SEVERITIES = ("low", "medium", "high", "critical")
MENTION_MODES = ("none", "author", "codeowners", "list")
ROLES = ("author", "reviewer", "other")


class ConfigError(ValueError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class PathsCfg:
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ("**/target/**", "**/build/**", "**/node_modules/**")


@dataclass(frozen=True)
class MentionsCfg:
    mode: tuple[str, ...] = ("none",)
    users: tuple[str, ...] = ()
    min_severity: str = "high"


@dataclass(frozen=True)
class RepoConfig:
    version: int = 1
    enabled: bool = True
    mode: str = "comment"
    display: str = "B"
    paths: PathsCfg = field(default_factory=PathsCfg)
    min_severity: str = "low"
    secrets: bool = True
    mentions: MentionsCfg = field(default_factory=MentionsCfg)
    trusted_roles: tuple[str, ...] = ("author", "reviewer")
    check_run: bool = True
    max_changed_files: int = 300
    max_findings: int = 40


def _strs(v: Any, key: str, problems: list[str]) -> tuple[str, ...]:
    if isinstance(v, str):
        return (v,)
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return tuple(v)
    problems.append(f"{key}: phải là chuỗi hoặc danh sách chuỗi")
    return ()


def _section(
    raw: dict[str, Any], key: str, allowed: set[str], problems: list[str]
) -> dict[str, Any]:
    sec = raw.get(key, {})
    if sec is None:
        return {}
    if not isinstance(sec, dict):
        problems.append(f"{key}: phải là một mục có khóa con")
        return {}
    for k in sec:
        if k not in allowed:
            problems.append(f"{key}.{k}: khóa không được hỗ trợ")
    return sec


def _int(v: Any, key: str, lo: int, hi: int, problems: list[str], default: int) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        problems.append(f"{key}: số nguyên từ {lo} đến {hi}")
        return default
    return v


def parse_config(text: str | None) -> RepoConfig:
    if text is None or not text.strip():
        return RepoConfig()
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError([f"YAML sai cú pháp: {exc}"]) from exc
    if raw is None:
        return RepoConfig()
    if not isinstance(raw, dict):
        raise ConfigError(["gốc phải là một mục có khóa con"])
    problems: list[str] = []
    top = {"version", "enabled", "mode", "display", "paths", "severity", "secrets", "mentions",
           "feedback", "check_run", "limits"}  # fmt: skip
    for k in raw:
        if k not in top:
            problems.append(f"{k}: khóa không được hỗ trợ")
    d = RepoConfig()
    if raw.get("version", 1) != 1:
        problems.append("version: chỉ hỗ trợ 1")
    enabled = raw.get("enabled", d.enabled)
    if not isinstance(enabled, bool):
        problems.append("enabled: phải là true hoặc false")
        enabled = d.enabled
    mode = raw.get("mode", d.mode)
    if mode not in ("comment", "shadow"):
        problems.append("mode: comment hoặc shadow")
        mode = d.mode
    display = raw.get("display", d.display)
    if display not in ("A", "B", "C"):
        problems.append("display: A, B hoặc C")
        display = d.display

    p = _section(raw, "paths", {"include", "exclude"}, problems)
    paths = PathsCfg(
        include=_strs(p["include"], "paths.include", problems)
        if "include" in p
        else d.paths.include,
        exclude=_strs(p["exclude"], "paths.exclude", problems)
        if "exclude" in p
        else d.paths.exclude,
    )
    sev = _section(raw, "severity", {"min_comment"}, problems)
    min_sev = sev.get("min_comment", d.min_severity)
    if min_sev not in SEVERITIES:
        problems.append(f"severity.min_comment: một trong {', '.join(SEVERITIES)}")
        min_sev = d.min_severity
    sec = _section(raw, "secrets", {"enabled"}, problems)
    secrets = sec.get("enabled", d.secrets)
    if not isinstance(secrets, bool):
        problems.append("secrets.enabled: phải là true hoặc false")
        secrets = d.secrets
    m = _section(raw, "mentions", {"mode", "users", "min_severity"}, problems)
    modes = _strs(m["mode"], "mentions.mode", problems) if "mode" in m else d.mentions.mode
    for x in modes:
        if x not in MENTION_MODES:
            problems.append(
                f"mentions.mode: {x!r} không hợp lệ, chọn trong {', '.join(MENTION_MODES)}"
            )
    users = _strs(m["users"], "mentions.users", problems) if "users" in m else ()
    if any(not u.startswith("@") for u in users):
        problems.append("mentions.users: mỗi mục phải bắt đầu bằng @")
    if "list" in modes and not users:
        problems.append("mentions.mode có list nhưng mentions.users rỗng")
    msev = m.get("min_severity", d.mentions.min_severity)
    if msev not in SEVERITIES:
        problems.append(f"mentions.min_severity: một trong {', '.join(SEVERITIES)}")
        msev = d.mentions.min_severity
    fb = _section(raw, "feedback", {"trusted_roles"}, problems)
    roles = (
        _strs(fb["trusted_roles"], "feedback.trusted_roles", problems)
        if "trusted_roles" in fb
        else d.trusted_roles
    )
    for r in roles:
        if r not in ROLES:
            problems.append(
                f"feedback.trusted_roles: {r!r} không hợp lệ, chọn trong {', '.join(ROLES)}"
            )
    cr = _section(raw, "check_run", {"enabled"}, problems)
    check_run = cr.get("enabled", d.check_run)
    if not isinstance(check_run, bool):
        problems.append("check_run.enabled: phải là true hoặc false")
        check_run = d.check_run
    lim = _section(raw, "limits", {"max_changed_files", "max_findings"}, problems)
    max_files = (
        _int(
            lim["max_changed_files"],
            "limits.max_changed_files",
            1,
            5000,
            problems,
            d.max_changed_files,
        )
        if "max_changed_files" in lim
        else d.max_changed_files
    )
    max_find = (
        _int(lim["max_findings"], "limits.max_findings", 1, 500, problems, d.max_findings)
        if "max_findings" in lim
        else d.max_findings
    )
    if problems:
        raise ConfigError(problems)
    return RepoConfig(
        1, enabled, mode, display, paths, min_sev, secrets,
        MentionsCfg(modes, users, msev), roles, check_run, max_files, max_find,
    )  # fmt: skip
