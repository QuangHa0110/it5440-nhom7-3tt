"""Chạy công cụ quét và đọc SARIF."""

from pr_triage.scan.sarif import parse_sarif
from pr_triage.scan.semgrep import SemgrepAdapter

__all__ = ["SemgrepAdapter", "parse_sarif"]
