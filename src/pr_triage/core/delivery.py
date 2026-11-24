"""Yêu cầu quét chung cho mọi đường kích hoạt, danh sách repo cho phép và định tuyến (ADR 0018)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fnmatch import fnmatchcase


class Channel(StrEnum):
    """Đường kích hoạt. Thêm đường mới = thêm một giá trị và một lớp con của `Trigger`."""

    GITHUB_APP = "github-app"
    WEBHOOK = "webhook"  # webhook của máy chủ pr-triage cho GitLab, Gitea, Bitbucket (ADR 0021)
    JENKINS = "jenkins"


class DeliveryConfigError(ValueError):
    """Cấu hình danh sách cho phép hoặc định tuyến sai."""


@dataclass(frozen=True)
class ScanRequest:
    """Thứ duy nhất lõi cần biết về một lần kích hoạt, bất kể nó đến từ đâu."""

    repo: str
    pr_number: int
    head_sha: str
    channel: Channel
    base_ref: str = ""
    draft: bool = False


def _matches(repo: str, pattern: str) -> bool:
    return fnmatchcase(repo.lower(), pattern.lower())


def split_csv(raw: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in raw.split(",") if x.strip())


@dataclass(frozen=True)
class RepoAllowList:
    """Danh sách mẫu `owner/repo` (khớp kiểu shell, không phân biệt hoa thường).

    `empty_allows_all` nói rõ danh sách rỗng nghĩa là gì: GitHub App giữ `True` (tương thích),
    Jenkins dùng `False` vì webhook cấp tổ chức gửi sự kiện của mọi repo.
    """

    patterns: tuple[str, ...] = ()
    empty_allows_all: bool = True

    @classmethod
    def from_csv(cls, raw: str, empty_allows_all: bool = True) -> RepoAllowList:
        return cls(split_csv(raw), empty_allows_all)

    def allows(self, repo: str) -> bool:
        if not self.patterns:
            return self.empty_allows_all
        return any(_matches(repo, p) for p in self.patterns)

    def exact_names(self) -> tuple[str, ...]:
        """Các mẫu là tên đầy đủ (không ký tự đại diện), dùng được để hỏi GitHub từng repo."""
        return tuple(p for p in self.patterns if not any(c in p for c in "*?["))


@dataclass(frozen=True)
class RouteRule:
    channel: Channel
    pattern: str


@dataclass(frozen=True)
class RoutePolicy:
    """Mỗi repo chỉ thuộc về một kênh. Không đặt luật nào thì mọi kênh đều được.

    Đã có luật: repo không khớp luật nào bị từ chối; repo khớp luật của hai kênh khác nhau bị
    từ chối ở cả hai (đóng khi mơ hồ).
    """

    rules: tuple[RouteRule, ...] = ()

    @classmethod
    def parse(cls, raw: str) -> RoutePolicy:
        rules: list[RouteRule] = []
        seen: dict[str, Channel] = {}
        for item in split_csv(raw):
            name, sep, pattern = item.partition(":")
            if not sep or not pattern.strip():
                raise DeliveryConfigError(f"luật định tuyến sai '{item}', cần dạng kênh:mẫu")
            try:
                channel = Channel(name.strip())
            except ValueError:
                valid = ", ".join(c.value for c in Channel)
                raise DeliveryConfigError(f"kênh '{name}' không có, chọn: {valid}") from None
            key = pattern.strip().lower()
            if key in seen and seen[key] is not channel:
                raise DeliveryConfigError(
                    f"mẫu '{pattern.strip()}' gán cho cả {seen[key].value} và {channel.value}"
                )
            seen[key] = channel
            rules.append(RouteRule(channel, pattern.strip()))
        return cls(tuple(rules))

    def channels_for(self, repo: str) -> frozenset[Channel]:
        if not self.rules:
            return frozenset(Channel)
        return frozenset(r.channel for r in self.rules if _matches(repo, r.pattern))

    def permits(self, channel: Channel, repo: str) -> bool:
        if not self.rules:
            return True
        owners = self.channels_for(repo)
        return len(owners) == 1 and channel in owners


@dataclass(frozen=True)
class RepoGate:
    """Cổng chung: repo phải nằm trong danh sách cho phép và được định tuyến cho kênh này."""

    allow: RepoAllowList
    routes: RoutePolicy = RoutePolicy()

    def admits(self, channel: Channel, repo: str) -> bool:
        return self.allow.allows(repo) and self.routes.permits(channel, repo)
