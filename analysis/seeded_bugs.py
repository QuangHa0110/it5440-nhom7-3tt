"""Bộ lỗi gieo có kiểm soát cho Java (CWE-89): sinh mã, quét và đo bộ trích ngữ cảnh.

Mỗi ca là một file Java nhỏ có đúng một hàm xử lý. Nhãn đáp án được quyết định lúc sinh mã,
không do người hay AI gán: mẫu `vuln` có lỗi thật, mẫu `safe` là đối chứng đã được làm sạch
hoặc tham số hóa đúng cách. Mỗi mẫu thay đổi cách dữ liệu đi từ request tới câu truy vấn, nên kết quả
tách được theo dạng luồng dữ liệu (trực tiếp, qua biến, qua StringBuilder, qua hàm phụ, qua trường...).

Giới hạn thống kê: các ca trong cùng một mẫu chỉ khác tên định danh (tên biến, bảng, cột), nên đơn vị
độc lập là mẫu (11), không phải ca. Báo cáo theo từng mẫu, không gộp tất cả ca để tính khoảng tin cậy.

Phần sinh mã không import gì từ `pr_triage`. Chỉ lệnh `scan` mới dùng `pr_triage` như thư viện.

    python -m analysis.seeded_bugs generate --out /tmp/seeded --seed 0 --per-cell 5
    python -m analysis.seeded_bugs scan --corpus /tmp/seeded --out /tmp/seeded/results.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from string import Template

CWE = "CWE-89"
PACKAGE = "seeded"
REPO = Path(__file__).resolve().parents[1]
DEFAULT_RULES = REPO / "configs" / "semgrep" / "java-injection.yml"
DEFAULT_CATALOG = REPO / "configs" / "context" / "java.yml"

HEADER = """package seeded;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Set;
import javax.servlet.http.HttpServletRequest;

public class $cls {
$body
}
"""


@dataclass(frozen=True)
class Pattern:
    name: str
    group: str  # direct | intra | inter | field | sanitize
    note: str
    vuln: str
    safe: str


@dataclass(frozen=True)
class Case:
    case_id: str
    file: str
    cwe: str
    pattern: str
    group: str
    variant: str  # vuln | safe
    truth: str  # true | false
    seed: int
    sink_line: int  # dòng chứa lời gọi executeQuery, dùng để thử bộ trích ngữ cảnh độc lập với công cụ quét


PATTERNS: tuple[Pattern, ...] = (
    Pattern(
        "direct_concat",
        "direct",
        "nối chuỗi ngay tại lời gọi so với PreparedStatement",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        Statement $st = $conn.createStatement();
        return $st.executeQuery("SELECT * FROM $tbl WHERE $col = '" + $req.getParameter("$param") + "'");
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        PreparedStatement $st = $conn.prepareStatement("SELECT * FROM $tbl WHERE $col = ?");
        $st.setString(1, $req.getParameter("$param"));
        return $st.executeQuery();
    }""",
    ),
    Pattern(
        "local_var",
        "intra",
        "qua biến cục bộ; đối chứng ép kiểu số bằng Integer.parseInt",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        String $q = "SELECT * FROM $tbl WHERE $col = '" + $v + "'";
        return $conn.createStatement().executeQuery($q);
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        int $v = Integer.parseInt($req.getParameter("$param"));
        String $q = "SELECT * FROM $tbl WHERE id = " + $v;
        return $conn.createStatement().executeQuery($q);
    }""",
    ),
    Pattern(
        "string_builder",
        "intra",
        "qua StringBuilder.append; đối chứng chỉ nối hằng và dùng tham số ?",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        StringBuilder $sb = new StringBuilder("SELECT * FROM $tbl WHERE $col = '");
        $sb.append($v);
        $sb.append("'");
        return $conn.createStatement().executeQuery($sb.toString());
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        StringBuilder $sb = new StringBuilder("SELECT * FROM $tbl WHERE ");
        $sb.append("$col = ?");
        PreparedStatement $st = $conn.prepareStatement($sb.toString());
        $st.setString(1, $req.getParameter("$param"));
        return $st.executeQuery();
    }""",
    ),
    Pattern(
        "string_format",
        "intra",
        "qua String.format với %s; đối chứng dùng %d sau Integer.parseInt",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        String $q = String.format("SELECT * FROM $tbl WHERE $col = '%s'", $v);
        return $conn.createStatement().executeQuery($q);
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        int $v = Integer.parseInt($req.getParameter("$param"));
        String $q = String.format("SELECT * FROM $tbl WHERE id = %d", $v);
        return $conn.createStatement().executeQuery($q);
    }""",
    ),
    Pattern(
        "helper_return",
        "inter",
        "câu truy vấn dựng trong hàm phụ trả về; đối chứng hàm phụ trả hằng",
        """\
    private String $helper(String $v) {
        return "SELECT * FROM $tbl WHERE $col = '" + $v + "'";
    }

    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        return $conn.createStatement().executeQuery($helper($req.getParameter("$param")));
    }""",
        """\
    private String $helper(String $v) {
        return "SELECT * FROM $tbl WHERE $col = 'fixed'";
    }

    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        return $conn.createStatement().executeQuery($helper($req.getParameter("$param")));
    }""",
    ),
    Pattern(
        "param_from_caller",
        "inter",
        "hàm sink nhận tham số, nguồn nằm ở nơi gọi; đối chứng hàm sink tham số hóa",
        """\
    private ResultSet $helper(Connection $conn, String $v) throws SQLException {
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + $v + "'");
    }

    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        return $helper($conn, $req.getParameter("$param"));
    }""",
        """\
    private ResultSet $helper(Connection $conn, String $v) throws SQLException {
        PreparedStatement $st = $conn.prepareStatement("SELECT * FROM $tbl WHERE $col = ?");
        $st.setString(1, $v);
        return $st.executeQuery();
    }

    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        return $helper($conn, $req.getParameter("$param"));
    }""",
    ),
    Pattern(
        "field_flow",
        "field",
        "dữ liệu đi qua trường của đối tượng; đối chứng trường được gán hằng",
        """\
    private String $fld;

    public void bind(HttpServletRequest $req) {
        this.$fld = $req.getParameter("$param");
    }

    public ResultSet run(Connection $conn) throws SQLException {
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + this.$fld + "'");
    }""",
        """\
    private String $fld;

    public void bind(HttpServletRequest $req) {
        this.$fld = "default";
    }

    public ResultSet run(Connection $conn) throws SQLException {
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + this.$fld + "'");
    }""",
    ),
    Pattern(
        "weak_vs_strong_sanitizer",
        "sanitize",
        "ngữ cảnh số: replace dấu nháy không đủ, so với Long.parseLong",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param").replace("'", "");
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE id = " + $v);
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        long $v = Long.parseLong($req.getParameter("$param"));
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE id = " + $v);
    }""",
    ),
    Pattern(
        "weak_vs_strong_validation",
        "sanitize",
        "kiểm tra chỉ độ dài so với kiểm tra bằng regex ký tự an toàn",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        if ($v.length() > 50) {
            throw new IllegalArgumentException("too long");
        }
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + $v + "'");
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        if (!$v.matches("[A-Za-z0-9_]{1,50}")) {
            throw new IllegalArgumentException("invalid");
        }
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + $v + "'");
    }""",
    ),
    Pattern(
        "overwrite_cond_vs_always",
        "intra",
        "biến bị ghi đè có điều kiện (còn lỗi) so với ghi đè vô điều kiện (hết lỗi)",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        if ($req.getParameter("debug") == null) {
            $v = "default";
        }
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + $v + "'");
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        $v = "default";
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl WHERE $col = '" + $v + "'");
    }""",
    ),
    Pattern(
        "allowlist_order_by",
        "sanitize",
        "ORDER BY lấy từ request: không kiểm tra so với danh sách cho phép",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        String $v = $req.getParameter("$param");
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl ORDER BY " + $v);
    }""",
        """\
    public ResultSet handle(HttpServletRequest $req, Connection $conn) throws SQLException {
        Set<String> $allowed = Set.of("id", "$col");
        String $v = $req.getParameter("$param");
        String $order = $allowed.contains($v) ? $v : "id";
        return $conn.createStatement().executeQuery("SELECT * FROM $tbl ORDER BY " + $order);
    }""",
    ),
)

_POOLS: dict[str, tuple[str, ...]] = {
    "req": ("req", "request", "httpReq"),
    "conn": ("conn", "connection", "db"),
    "st": ("st", "stmt", "statement"),
    "v": ("v", "input", "raw", "value", "term"),
    "q": ("q", "sql", "query"),
    "sb": ("sb", "buf", "builder"),
    "param": ("name", "id", "user", "search", "sort", "term", "key"),
    "tbl": ("users", "orders", "items", "accounts", "events", "tickets"),
    "col": ("name", "owner", "title", "code", "label"),
    "helper": ("buildQuery", "lookup", "fetchRows", "findBy", "queryFor"),
    "fld": ("pending", "criteria", "filter", "needle"),
    "allowed": ("allowed", "whitelist", "columns"),
    "order": ("order", "sortBy", "column"),
}


def _rng(seed: int, pattern: str, variant: str, index: int) -> random.Random:
    return random.Random(f"{seed}:{pattern}:{variant}:{index}")


def render(pattern: Pattern, variant: str, seed: int, index: int) -> tuple[str, str]:
    """Trả về (tên lớp, mã Java). Cùng tham số cho cùng kết quả."""
    rng = _rng(seed, pattern.name, variant, index)
    names = {k: rng.choice(v) for k, v in _POOLS.items()}
    body = Template(pattern.vuln if variant == "vuln" else pattern.safe).substitute(names)
    cls = f"Case{pattern.name.title().replace('_', '')}{variant.title()}{index:02d}"
    return cls, Template(HEADER).substitute(cls=cls, body=body)


def _sink_line(code: str) -> int:
    for no, line in enumerate(code.splitlines(), 1):
        if ".executeQuery(" in line:
            return no
    raise ValueError("mẫu không có lời gọi executeQuery")


def build_cases(seed: int, per_cell: int) -> list[tuple[Case, str]]:
    out: list[tuple[Case, str]] = []
    for pat in PATTERNS:
        for variant in ("vuln", "safe"):
            for i in range(per_cell):
                cls, code = render(pat, variant, seed, i)
                case = Case(
                    case_id=f"sqli-{pat.name}-{variant}-{i:02d}",
                    file=f"src/{PACKAGE}/{cls}.java",
                    cwe=CWE,
                    pattern=pat.name,
                    group=pat.group,
                    variant=variant,
                    truth="true" if variant == "vuln" else "false",
                    seed=seed,
                    sink_line=_sink_line(code),
                )
                out.append((case, code))
    return out


def generate(
    out: Path, seed: int = 0, per_cell: int = 5, init_git: bool = True, force: bool = False
) -> list[Case]:
    if per_cell < 1:
        raise ValueError("per_cell phải >= 1")
    corpus = out / "corpus"
    if corpus.exists():
        if not force:
            raise FileExistsError(f"{corpus} đã tồn tại; dùng --force để xóa và sinh lại")
        shutil.rmtree(corpus)
    cases = build_cases(seed, per_cell)
    for case, code in cases:
        path = corpus / case.file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, "utf-8")
    manifest = {
        "cwe": CWE,
        "seed": seed,
        "per_cell": per_cell,
        "cases": [asdict(c) for c, _ in cases],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), "utf-8")
    if init_git:
        _git_commit(corpus)
    return [c for c, _ in cases]


def _git_commit(corpus: Path) -> None:
    ident = [
        "-c", "user.name=seeded-bugs",
        "-c", "user.email=seeded@example.invalid",
        "-c", "commit.gpgsign=false",
    ]  # fmt: skip

    def git(*args: str) -> None:
        subprocess.run(["git", *ident, *args], cwd=corpus, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "seeded corpus")


def load_manifest(out: Path) -> list[Case]:
    data = json.loads((out / "manifest.json").read_text("utf-8"))
    return [Case(**c) for c in data["cases"]]


@dataclass
class Row:
    case_id: str
    pattern: str
    group: str
    variant: str
    truth: str
    n_findings: int  # số cảnh báo công cụ quét báo trong file của ca
    probe_source: bool  # bộ trích C tìm được nguồn khi đặt tại dòng sink thật
    probe_sink: bool
    probe_missing_n: int
    probe_slices: int


def scan(
    out: Path,
    rules: Sequence[str],
    catalog: Path,
    max_ms: int = 5000,
) -> list[Row]:
    """Quét bằng Semgrep, rồi thử bộ trích C tại dòng sink thật của mọi ca.

    Phép thử bộ trích không phụ thuộc việc công cụ quét có báo hay không, nên đo riêng được
    độ phủ của bộ trích C theo dạng luồng dữ liệu. Dùng `pr_triage` như thư viện, chỉ đọc.
    """
    from pr_triage.context import DataflowProvider, SymbolIndex, load_catalog
    from pr_triage.core.models import RawFinding
    from pr_triage.normalize import to_findings
    from pr_triage.scan.semgrep import SemgrepAdapter

    corpus = out / "corpus"
    cases = load_manifest(out)
    flagged: dict[str, int] = defaultdict(int)
    for raw in SemgrepAdapter(list(rules)).scan(corpus):
        flagged[Path(raw.file).as_posix()] += 1
    probes = [
        RawFinding(
            "seeded-probe", "seeded-probe", "probe", "high", c.file, c.sink_line, c.sink_line, CWE
        )
        for c in cases
    ]
    index = SymbolIndex(corpus)
    findings = to_findings(probes, corpus, index.enclosing_symbol)
    provider = DataflowProvider(load_catalog(catalog), max_ms=max_ms)
    by_file = {Path(f.file).as_posix(): provider.extract(f, corpus) for f in findings}
    rows: list[Row] = []
    for case in cases:
        bundle = by_file[Path(case.file).as_posix()]
        rows.append(
            Row(
                case_id=case.case_id,
                pattern=case.pattern,
                group=case.group,
                variant=case.variant,
                truth=case.truth,
                n_findings=flagged.get(Path(case.file).as_posix(), 0),
                probe_source=bool(bundle.source),
                probe_sink=bool(bundle.sink),
                probe_missing_n=len(bundle.missing),
                probe_slices=len(bundle.slices),
            )
        )
    return rows


def write_csv(rows: Iterable[Row], path: Path) -> None:
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(asdict(rows[0])) if rows else [])
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def summarize(rows: Sequence[Row]) -> str:
    """Hai phép đo tách biệt: công cụ quét có báo không, và bộ trích C có tìm được nguồn không."""
    by: dict[tuple[str, str], list[Row]] = defaultdict(list)
    for r in rows:
        by[(r.pattern, r.variant)].append(r)
    lines = [
        "| Mẫu | Loại | Số ca | Công cụ quét báo | Bộ trích C thấy nguồn | Thấy sink |",
        "|---|---|---|---|---|---|",
    ]
    for (pattern, variant), rs in sorted(by.items()):
        lines.append(
            f"| {pattern} | {variant} | {len(rs)} | {sum(r.n_findings > 0 for r in rs)}/{len(rs)} "
            f"| {sum(r.probe_source for r in rs)}/{len(rs)} | {sum(r.probe_sink for r in rs)}/{len(rs)} |"
        )
    vuln = [r for r in rows if r.variant == "vuln"]
    safe = [r for r in rows if r.variant == "safe"]
    pv = {p for p, v in by if v == "vuln"}
    ps = {p for p, v in by if v == "safe"}

    def all_of(pattern: str, variant: str, field: str) -> bool:
        return all(bool(getattr(r, field)) for r in by[(pattern, variant)])

    lines += [
        "",
        f"Theo ca: công cụ quét báo {sum(r.n_findings > 0 for r in vuln)}/{len(vuln)} ca có lỗi thật "
        f"và báo nhầm {sum(r.n_findings > 0 for r in safe)}/{len(safe)} ca đã an toàn; "
        f"bộ trích C thấy nguồn ở {sum(r.probe_source for r in vuln)}/{len(vuln)} ca có lỗi thật.",
        f"Theo mẫu (đơn vị độc lập): công cụ quét báo đủ mọi ca ở "
        f"{sum(all_of(p, 'vuln', 'n_findings') for p in pv)}/{len(pv)} mẫu có lỗi và "
        f"{sum(all_of(p, 'safe', 'n_findings') for p in ps)}/{len(ps)} mẫu an toàn; "
        f"bộ trích C thấy nguồn ở mọi ca của {sum(all_of(p, 'vuln', 'probe_source') for p in pv)}/{len(pv)} mẫu có lỗi.",
        "Lưu ý: các ca trong cùng mẫu chỉ khác tên định danh, không độc lập; không tính khoảng tin cậy trên số ca.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="seeded_bugs", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="sinh corpus và manifest")
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--per-cell", type=int, default=5)
    g.add_argument("--no-git", action="store_true", help="không khởi tạo repo git cho corpus")
    g.add_argument("--force", action="store_true", help="xóa corpus cũ rồi sinh lại")
    s = sub.add_parser("scan", help="quét corpus và đo bộ trích C")
    s.add_argument("--corpus", type=Path, required=True, help="thư mục --out của lệnh generate")
    s.add_argument("--rules", action="append", default=None)
    s.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    s.add_argument("--out", type=Path, default=None, help="ghi CSV từng ca")
    args = ap.parse_args(argv)
    if args.cmd == "generate":
        try:
            cases = generate(args.out, args.seed, args.per_cell, not args.no_git, args.force)
        except FileExistsError as exc:
            print(exc, file=sys.stderr)
            return 2
        print(f"đã sinh {len(cases)} ca tại {args.out / 'corpus'}")
        return 0
    rules = args.rules or [str(DEFAULT_RULES)]
    rows = scan(args.corpus, rules, args.catalog)
    if args.out:
        write_csv(rows, args.out)
    sys.stdout.write(summarize(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
