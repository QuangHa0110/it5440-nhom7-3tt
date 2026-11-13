"""Điểm vào dòng lệnh `pr-triage`."""

import argparse

from pr_triage import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr-triage", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
