import json
import subprocess
from pathlib import Path

import pytest
import tree_sitter_java
from tree_sitter import Language, Parser

from analysis import seeded_bugs as sb

CATALOG = sb.DEFAULT_CATALOG
RULES = sb.DEFAULT_RULES


def test_generation_is_deterministic_and_seed_sensitive() -> None:
    a = [code for _, code in sb.build_cases(seed=3, per_cell=2)]
    assert a == [code for _, code in sb.build_cases(seed=3, per_cell=2)]
    assert a != [code for _, code in sb.build_cases(seed=4, per_cell=2)]


def test_case_count_ids_and_truth() -> None:
    cases = [c for c, _ in sb.build_cases(seed=0, per_cell=3)]
    assert len(cases) == len(sb.PATTERNS) * 2 * 3
    assert len({c.case_id for c in cases}) == len(cases)
    assert len({c.file for c in cases}) == len(cases)
    assert all((c.truth == "true") == (c.variant == "vuln") for c in cases)


def test_every_pattern_has_distinct_vuln_and_safe_bodies() -> None:
    for p in sb.PATTERNS:
        assert p.vuln != p.safe, p.name


def test_generated_code_is_complete_java() -> None:
    parser = Parser(Language(tree_sitter_java.language()))
    for case, code in sb.build_cases(seed=0, per_cell=2):
        assert "$" not in code, case.case_id
        assert not parser.parse(code.encode()).root_node.has_error, case.case_id


def test_sink_line_points_at_execute_query() -> None:
    for case, code in sb.build_cases(seed=0, per_cell=1):
        assert ".executeQuery(" in code.splitlines()[case.sink_line - 1], case.case_id


def test_generate_writes_manifest_files_and_git_commit(tmp_path: Path) -> None:
    cases = sb.generate(tmp_path, seed=1, per_cell=1)
    corpus = tmp_path / "corpus"
    assert all((corpus / c.file).is_file() for c in cases)
    manifest = json.loads((tmp_path / "manifest.json").read_text("utf-8"))
    assert len(manifest["cases"]) == len(cases)
    assert sb.load_manifest(tmp_path) == cases
    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=corpus, capture_output=True, text=True, check=True
    )
    assert len(log.stdout.splitlines()) == 1


def test_generate_without_git(tmp_path: Path) -> None:
    sb.generate(tmp_path, per_cell=1, init_git=False)
    assert not (tmp_path / "corpus" / ".git").exists()


def test_regenerate_requires_force_and_leaves_no_stale_files(tmp_path: Path) -> None:
    sb.generate(tmp_path, per_cell=2)
    with pytest.raises(FileExistsError):
        sb.generate(tmp_path, per_cell=1)
    cases = sb.generate(tmp_path, per_cell=1, force=True)
    on_disk = sorted(p.name for p in (tmp_path / "corpus" / "src" / "seeded").glob("*.java"))
    assert on_disk == sorted(Path(c.file).name for c in cases)


def test_main_generate_reports_existing_corpus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert sb.main(["generate", "--out", str(tmp_path), "--per-cell", "1", "--no-git"]) == 0
    assert sb.main(["generate", "--out", str(tmp_path), "--per-cell", "1", "--no-git"]) == 2
    assert "--force" in capsys.readouterr().err


def test_write_csv_roundtrip(tmp_path: Path) -> None:
    import csv

    rows = [sb.Row("a", "p", "g", "vuln", "true", 2, True, True, 1, 3)]
    path = tmp_path / "r.csv"
    sb.write_csv(rows, path)
    got = list(csv.DictReader(path.open(encoding="utf-8")))
    assert (
        got[0]["case_id"] == "a"
        and got[0]["n_findings"] == "2"
        and got[0]["probe_source"] == "True"
    )


def test_generate_rejects_empty_cells(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="per_cell"):
        sb.generate(tmp_path, per_cell=0)


def test_summarize_counts() -> None:
    def row(variant: str, flagged: int, source: bool) -> sb.Row:
        return sb.Row("id", "p", "g", variant, "x", flagged, source, True, 0, 1)

    text = sb.summarize([row("vuln", 1, True), row("vuln", 0, False), row("safe", 2, True)])
    assert "báo 1/2 ca có lỗi thật" in text
    assert "báo nhầm 1/1 ca đã an toàn" in text
    assert "nguồn ở 1/2 ca có lỗi thật" in text
    assert "đơn vị độc lập" in text and "không độc lập" in text


@pytest.fixture(scope="module")
def scanned(tmp_path_factory: pytest.TempPathFactory) -> dict[tuple[str, str], list[sb.Row]]:
    out = tmp_path_factory.mktemp("seeded")
    sb.generate(out, seed=0, per_cell=1)
    by: dict[tuple[str, str], list[sb.Row]] = {}
    for r in sb.scan(out, [str(RULES)], CATALOG):
        by.setdefault((r.pattern, r.variant), []).append(r)
    return by


def test_scanner_flags_direct_concat_but_not_prepared(
    scanned: dict[tuple[str, str], list[sb.Row]],
) -> None:
    assert all(r.n_findings > 0 for r in scanned[("direct_concat", "vuln")])
    assert all(r.n_findings == 0 for r in scanned[("direct_concat", "safe")])


@pytest.mark.parametrize("pattern", ["direct_concat", "local_var", "helper_return"])
def test_context_extractor_finds_source_for_covered_flows(
    scanned: dict[tuple[str, str], list[sb.Row]], pattern: str
) -> None:
    assert all(r.probe_source for r in scanned[(pattern, "vuln")])


@pytest.mark.xfail(strict=True, reason="bộ trích C chưa theo dõi luồng qua append/add/put")
def test_context_extractor_follows_string_builder(
    scanned: dict[tuple[str, str], list[sb.Row]],
) -> None:
    assert all(r.probe_source for r in scanned[("string_builder", "vuln")])


@pytest.mark.xfail(strict=True, reason="bộ trích C chưa theo dõi luồng qua trường của đối tượng")
def test_context_extractor_follows_fields(
    scanned: dict[tuple[str, str], list[sb.Row]],
) -> None:
    assert all(r.probe_source for r in scanned[("field_flow", "vuln")])
