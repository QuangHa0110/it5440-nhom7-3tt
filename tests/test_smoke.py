from pr_triage import __version__
from pr_triage.cli import main


def test_version_is_semver() -> None:
    assert len(__version__.split(".")) == 3


def test_cli_runs() -> None:
    assert main([]) == 0
