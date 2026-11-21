"""Cấu hình chung cho mọi test."""

import pytest


@pytest.fixture(autouse=True)
def _no_local_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Không để `.env` của máy cá nhân lọt vào test khi gọi `cli.main`."""
    monkeypatch.setenv("PR_TRIAGE_NO_DOTENV", "1")
