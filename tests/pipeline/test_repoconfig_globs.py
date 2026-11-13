import pytest

from pr_triage.pipeline import codeowners
from pr_triage.pipeline.pathglob import any_match, matches
from pr_triage.pipeline.repoconfig import ConfigError, RepoConfig, parse_config


def test_defaults_when_missing_or_empty() -> None:
    assert (
        parse_config(None) == RepoConfig() == parse_config("") == parse_config("# chỉ chú thích\n")
    )
    assert parse_config(None).mentions.mode == ("none",) and parse_config(None).enabled


def test_full_valid_config() -> None:
    c = parse_config(
        """
version: 1
enabled: true
mode: shadow
display: C
paths: {include: [src/**], exclude: ["**/test/**"]}
severity: {min_comment: medium}
secrets: {enabled: false}
mentions: {mode: [author, codeowners, list], users: ["@sec-team"], min_severity: critical}
feedback: {trusted_roles: [reviewer]}
check_run: {enabled: false}
limits: {max_changed_files: 50, max_findings: 5}
"""
    )
    assert (c.mode, c.display, c.min_severity, c.secrets, c.check_run) == (
        "shadow",
        "C",
        "medium",
        False,
        False,
    )
    assert c.paths.include == ("src/**",) and c.mentions.users == ("@sec-team",)
    assert c.trusted_roles == ("reviewer",) and (c.max_changed_files, c.max_findings) == (50, 5)


@pytest.mark.parametrize(
    "text,needle",
    [
        ("lạ: 1", "lạ: khóa không được hỗ trợ"),
        ("mode: block", "mode:"),
        ("display: Z", "display:"),
        ("paths: {glob: x}", "paths.glob"),
        ("severity: {min_comment: nghiêm-trọng}", "severity.min_comment"),
        ("mentions: {mode: list}", "mentions.users rỗng"),
        ("mentions: {mode: [list], users: [bob]}", "bắt đầu bằng @"),
        ("mentions: {mode: loa}", "không hợp lệ"),
        ("feedback: {trusted_roles: [admin]}", "không hợp lệ"),
        ("limits: {max_findings: 0}", "limits.max_findings"),
        ("limits: {max_findings: true}", "limits.max_findings"),
        ("enabled: có", "enabled:"),
        ("version: 2", "version:"),
        ("- danh sách", "gốc phải là"),
        ("a: [unclosed", "YAML sai cú pháp"),
    ],
)
def test_invalid_config_is_rejected_with_clear_message(text: str, needle: str) -> None:
    with pytest.raises(ConfigError) as e:
        parse_config(text)
    assert needle in str(e.value)


def test_all_problems_reported_together() -> None:
    with pytest.raises(ConfigError) as e:
        parse_config("mode: x\ndisplay: y\nlạ: 1")
    assert len(e.value.problems) == 3


@pytest.mark.parametrize(
    "pattern,path,expected",
    [
        ("**/test/**", "src/test/A.java", True),
        ("**/test/**", "test/A.java", True),
        ("**/test/**", "src/main/A.java", False),
        ("*.md", "docs/readme.md", True),
        ("*.md", "readme.md", True),
        ("/*.md", "docs/readme.md", False),
        ("docs/", "docs/a/b.txt", True),
        ("docs/", "x/docs/a.txt", True),
        ("/docs/", "x/docs/a.txt", False),
        ("/docs/", "docs/a.txt", True),
        ("src/*.java", "src/A.java", True),
        ("src/*.java", "src/sub/A.java", False),
        ("src/**/*.java", "src/sub/deep/A.java", True),
        ("Makefile", "any/dir/Makefile", True),
        ("a?c", "abc", True),
        ("a?c", "a/c", False),
    ],
)
def test_globs(pattern: str, path: str, expected: bool) -> None:
    assert matches(pattern, path) is expected


def test_any_match_and_windows_paths() -> None:
    assert any_match(["x/**", "y/**"], "y\\z.txt") and not any_match([], "a")


CODEOWNERS = """
# chú thích
*                     @org/everyone
/src/security/        @sec-lead @org/sec
*.sql                 @dba
/docs/                @docs-team
src/legacy/**         @legacy-owner  # ghi chú cuối dòng
!ignored              @nobody
[Section]
"""


def test_codeowners_last_match_wins_and_dedupes() -> None:
    rules = codeowners.parse(CODEOWNERS)
    assert codeowners.owners_for(["src/security/Auth.java"], rules) == ["@sec-lead", "@org/sec"]
    assert codeowners.owners_for(["db/schema.sql"], rules) == ["@dba"]
    assert codeowners.owners_for(["src/legacy/a/B.java"], rules) == ["@legacy-owner"]
    assert codeowners.owners_for(["README.txt"], rules) == ["@org/everyone"]
    both = codeowners.owners_for(["db/a.sql", "x/y.sql", "docs/z.md"], rules)
    assert both == ["@dba", "@docs-team"]
    assert codeowners.owners_for(["a"], []) == []
