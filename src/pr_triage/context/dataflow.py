"""Cách C: ngữ cảnh luồng dữ liệu cho Java (sơ đồ 6, ADR 0003 và 0005).

Lần ngược từ sink về nguồn bằng cú pháp (tree-sitter), tối đa `max_hops` bước gọi, và ghi rõ vào
`missing` mọi chỗ không lần ra. Ý tưởng dựng ngữ cảnh tất định lấy từ sift-sast (Apache-2.0),
danh mục nguồn, sink, hàm làm sạch lấy ý tưởng từ IRIS (MIT). Không sao chép mã.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node

from pr_triage.context.bundle import make_bundle
from pr_triage.context.catalog import Catalog
from pr_triage.context.snippet import read_lines
from pr_triage.context.symbols import JavaFile, SymbolIndex
from pr_triage.core.models import ContextBundle, ContextSlice, Finding, Variant

_PRIORITY = {
    "sink-function": 0,
    "sanitizer-candidate": 1,
    "callee": 2,
    "source-site": 3,
    "caller": 4,
}
_INVOKE = {"method_invocation", "object_creation_expression"}


@dataclass
class _Slice:
    file: str
    start: int
    end: int
    role: str


def _walk(node: Node) -> list[Node]:
    out: list[Node] = []
    stack = [node]
    while stack:
        n = stack.pop()
        out.append(n)
        stack.extend(reversed(n.children))
    return out


def _idents(jf: JavaFile, node: Node) -> list[str]:
    """Tên biến xuất hiện trong biểu thức, bỏ tên phương thức được gọi và tên trường."""
    names: list[str] = []

    def rec(n: Node) -> None:
        if n.type == "identifier":
            names.append(jf.text(n))
            return
        if n.type == "method_invocation":
            for field in ("object", "arguments"):
                child = n.child_by_field_name(field)
                if child is not None:
                    rec(child)
            return
        if n.type == "field_access":
            obj = n.child_by_field_name("object")
            if obj is not None:
                rec(obj)
            return
        if n.type in ("string_literal", "character_literal"):
            return
        for c in n.children:
            rec(c)

    rec(node)
    return list(dict.fromkeys(names))


def _invocations(node: Node) -> list[Node]:
    return [n for n in _walk(node) if n.type in _INVOKE]


def _call_name(jf: JavaFile, inv: Node) -> str:
    if inv.type == "method_invocation":
        return jf.text(inv.child_by_field_name("name"))
    return jf.text(inv.child_by_field_name("type"))


def _args(inv: Node) -> list[Node]:
    al = inv.child_by_field_name("arguments")
    return list(al.named_children) if al is not None else []


def _line(node: Node) -> int:
    return node.start_point[0] + 1


def _params(jf: JavaFile, method: Node) -> list[tuple[str, Node]]:
    pl = method.child_by_field_name("parameters")
    out: list[tuple[str, Node]] = []
    if pl is not None:
        for p in pl.named_children:
            if p.type in ("formal_parameter", "spread_parameter"):
                out.append((jf.text(p.child_by_field_name("name")), p))
    return out


def _annotation_names(jf: JavaFile, param: Node) -> list[str]:
    names: list[str] = []
    for n in _walk(param):
        if n.type in ("marker_annotation", "annotation"):
            nm = n.child_by_field_name("name")
            if nm is not None:
                names.append(jf.text(nm))
    return names


class _Run:
    def __init__(self, owner: DataflowProvider, index: SymbolIndex, finding: Finding) -> None:
        self.o = owner
        self.index = index
        self.finding = finding
        self.slices: list[_Slice] = []
        self.source: str | None = None
        self.sanitizers: list[str] = []
        self.missing: list[str] = []
        self.visited: dict[tuple[str, int, str], int] = {}
        self.deadline = time.monotonic() + owner.max_ms / 1000
        self.timed_out = False

    def note(self, text: str) -> None:
        if text not in self.missing:
            self.missing.append(text)

    def expired(self) -> bool:
        if time.monotonic() > self.deadline:
            if not self.timed_out:
                self.note("hết thời gian trích ngữ cảnh, phần còn lại bị bỏ")
            self.timed_out = True
        return self.timed_out

    def add_method_slice(
        self, jf: JavaFile, method: Node, role: str, focus: int | None = None
    ) -> None:
        start, end = _line(method), method.end_point[0] + 1
        cap = self.o.max_method_lines
        if end - start + 1 > cap:
            mid = focus or start
            start = max(start, mid - cap // 2)
            end = min(end, start + cap - 1)
        self.slices.append(_Slice(jf.rel_path, start, end, role))

    def set_source(self, kind: str, jf: JavaFile, node: Node) -> None:
        if self.source is None:
            self.source = f"{kind} ({jf.rel_path}:{_line(node)})"
        self.slices.append(_Slice(jf.rel_path, _line(node), node.end_point[0] + 1, "source-site"))

    def definitions(self, jf: JavaFile, method: Node, var: str, before_line: int) -> list[Node]:
        values: list[Node] = []
        for n in _walk(method):
            if _line(n) > before_line:
                continue
            if n.type == "variable_declarator":
                if jf.text(n.child_by_field_name("name")) == var and n.child_by_field_name("value"):
                    values.append(n.child_by_field_name("value"))  # type: ignore[arg-type]
            elif n.type == "assignment_expression":
                left = n.child_by_field_name("left")
                if left is not None and left.type == "identifier" and jf.text(left) == var:
                    right = n.child_by_field_name("right")
                    if right is not None:
                        values.append(right)
        return values

    def trace_var(self, jf: JavaFile, method: Node, var: str, before_line: int, hops: int) -> None:
        key = (jf.rel_path, method.start_byte, var)
        if self.visited.get(key, -1) >= hops or self.expired():
            return
        self.visited[key] = hops
        for value in self.definitions(jf, method, var, before_line):
            self.trace_expr(jf, method, value, _line(value), hops)
        for name, pnode in _params(jf, method):
            if name != var:
                continue
            ptype = jf.text(pnode.child_by_field_name("type"))
            if ptype.split(".")[-1] in self.o.catalog.framework_types:
                return
            for ann in _annotation_names(jf, pnode):
                kind = self.o.catalog.parameter_annotations.get(ann)
                if kind:
                    self.set_source(kind, jf, pnode)
                    return
            self.trace_to_callers(jf, method, name, hops)

    def trace_expr(
        self, jf: JavaFile, method: Node, expr: Node, before_line: int, hops: int
    ) -> None:
        kind = self.o.catalog.source_kind(jf.text(expr))
        if kind:
            self.set_source(kind, jf, expr)
        for inv in _invocations(expr):
            self.handle_callee(jf, inv, hops)
        for v in _idents(jf, expr):
            self.trace_var(jf, method, v, before_line, hops)

    def handle_callee(self, jf: JavaFile, inv: Node, hops: int) -> None:
        name = _call_name(jf, inv)
        looks = self.o.catalog.looks_like_sanitizer(name)
        if inv.type != "method_invocation" or self.expired():
            return
        argc = len(_args(inv))
        cands = [
            (cjf, m) for cjf, m in self.index.methods_named(name) if len(_params(cjf, m)) == argc
        ]
        if not cands:
            if looks:
                self.note(f"hàm {name} trông như hàm làm sạch nhưng không có mã nguồn trong repo")
                self.sanitizers.append(f"{name} (không có mã nguồn)")
            return
        same = [c for c in cands if c[0].rel_path == jf.rel_path]
        chosen = same[:1] or cands[: self.o.max_callers]
        if not same and len(cands) > 1:
            self.note(f"hàm {name}: {len(cands)} ứng viên trùng tên, lấy {len(chosen)}")
        if hops <= 0:
            self.note(f"hàm {name}: vượt giới hạn {self.o.max_hops} bước gọi")
            return
        for cjf, m in chosen:
            qualified = cjf.method_info(m).qualified
            role = "sanitizer-candidate" if looks else "callee"
            if looks:
                self.sanitizers.append(qualified)
            self.add_method_slice(cjf, m, role)
            for n in _walk(m):
                if n.type == "return_statement" and n.named_child_count:
                    self.trace_expr(cjf, m, n.named_children[0], _line(n), hops - 1)

    def trace_to_callers(self, jf: JavaFile, method: Node, param: str, hops: int) -> None:
        info = jf.method_info(method)
        if info.name in self.o.catalog.entry_points:
            return
        if hops <= 0:
            self.note(
                f"tham số {param} của {info.qualified}: vượt giới hạn {self.o.max_hops} bước gọi"
            )
            return
        idx = [n for n, _ in _params(jf, method)].index(param)
        total = len(_params(jf, method))
        calls = [
            (cjf, c)
            for cjf, c in self.index.calls_of(info.name)
            if len(_args(c)) == total
            and not (cjf is jf and method.start_byte <= c.start_byte <= method.end_byte)
        ]
        if len(self.index.methods_named(info.name)) > 1:
            self.note(f"tên hàm {info.name} trùng ở nhiều lớp, nơi gọi chỉ khớp theo tên")
        if not calls:
            self.note(f"không tìm thấy nơi gọi {info.qualified} trong repo")
            return
        if len(calls) > self.o.max_callers:
            self.note(f"{info.qualified} có {len(calls)} nơi gọi, lấy {self.o.max_callers}")
        for cjf, call in calls[: self.o.max_callers]:
            if self.expired():
                return
            cm = cjf.enclosing_method_node(_line(call))
            if cm is None:
                continue
            self.add_method_slice(cjf, cm, "caller", _line(call))
            arg = _args(call)[idx]
            self.trace_expr(cjf, cm, arg, _line(call), hops - 1)


class DataflowProvider:
    variant = Variant.C

    def __init__(
        self,
        catalog: Catalog,
        max_hops: int = 2,
        max_chars: int = 12000,
        max_callers: int = 3,
        max_ms: int = 5000,
        max_method_lines: int = 80,
    ) -> None:
        self.catalog = catalog
        self.max_hops = max_hops
        self.max_chars = max_chars
        self.max_callers = max_callers
        self.max_ms = max_ms
        self.max_method_lines = max_method_lines
        self._indexes: dict[Path, SymbolIndex] = {}

    def _index(self, root: Path) -> SymbolIndex:
        if root not in self._indexes:
            self._indexes[root] = SymbolIndex(root)
        return self._indexes[root]

    def _find_sink(self, jf: JavaFile, method: Node, f: Finding) -> Node | None:
        spec = self.catalog.sink_for(f.cwe)
        names = spec.methods if spec else self.catalog.any_sink_method()
        ctors = spec.constructors if spec else frozenset()
        cands: list[Node] = []
        for n in _walk(method):
            if n.type not in _INVOKE:
                continue
            first, last = _line(n), n.end_point[0] + 1
            if last < f.line_start or first > f.line_end:
                continue
            nm = _call_name(jf, n)
            if (n.type == "method_invocation" and nm in names) or (
                n.type == "object_creation_expression" and nm in ctors
            ):
                cands.append(n)
        return cands[0] if cands else None

    def extract(self, finding: Finding, checkout: Path) -> ContextBundle:
        t0 = time.monotonic()
        index = self._index(checkout)
        jf = index.file(finding.file)
        method = jf.enclosing_method_node(finding.line_start) if jf else None
        if jf is None or method is None:
            return self._fallback(
                finding,
                checkout,
                t0,
                "không xác định được hàm bao quanh, dùng ngữ cảnh quanh vị trí báo",
            )
        run = _Run(self, index, finding)
        run.add_method_slice(jf, method, "sink-function", finding.line_start)
        sink_node = self._find_sink(jf, method, finding)
        sink: str | None = None
        if sink_node is None:
            run.note("không xác định được sink theo danh mục, lần ngược từ dòng bị báo")
            node = jf.tree.root_node.descendant_for_point_range(
                (finding.line_start - 1, 0), (finding.line_start - 1, 0)
            )
            args = [node] if node is not None else []
            line = finding.line_start
        else:
            spec = self.catalog.sink_for(finding.cwe)
            kind = spec.kind if spec else "sink"
            sink = f"{kind}: {jf.rel_path}:{_line(sink_node)} {_call_name(jf, sink_node)}"
            args = _args(sink_node)
            receiver = sink_node.child_by_field_name("object")
            if not args and receiver is not None:
                args = [receiver]
            line = _line(sink_node)
        for arg in args:
            run.trace_expr(jf, method, arg, line, self.max_hops)
        if run.source is None and not run.timed_out:
            run.note("nguồn dữ liệu chưa xác định")
        slices = self._finalize(run, index)
        return make_bundle(
            Variant.C,
            finding.finding_id,
            slices,
            source=run.source,
            sink=sink,
            sanitizers=list(dict.fromkeys(run.sanitizers)),
            missing=run.missing,
            extract_ms=int((time.monotonic() - t0) * 1000),
        )

    def _fallback(self, f: Finding, checkout: Path, t0: float, why: str) -> ContextBundle:
        s, e, text = read_lines(checkout, f.file, f.line_start - 10, f.line_end + 10)
        return make_bundle(
            Variant.C,
            f.finding_id,
            [ContextSlice(f.file, s, e, "alert-site", text)],
            missing=[why],
            extract_ms=int((time.monotonic() - t0) * 1000),
        )

    def _finalize(self, run: _Run, index: SymbolIndex) -> list[ContextSlice]:
        merged: list[_Slice] = []
        by_file: dict[str, list[_Slice]] = {}
        for s in run.slices:
            by_file.setdefault(s.file, []).append(s)
        for file, items in by_file.items():
            items.sort(key=lambda s: s.start)
            cur = _Slice(file, items[0].start, items[0].end, items[0].role)
            for s in items[1:]:
                if s.start <= cur.end + 1:
                    cur.end = max(cur.end, s.end)
                    if _PRIORITY[s.role] < _PRIORITY[cur.role]:
                        cur.role = s.role
                else:
                    merged.append(cur)
                    cur = _Slice(file, s.start, s.end, s.role)
            merged.append(cur)
        merged.sort(key=lambda s: (_PRIORITY[s.role], s.file, s.start))
        out: list[ContextSlice] = []
        used = 0
        dropped = 0
        for s in merged:
            jf = index.file(s.file)
            text = jf.line_text(s.start, s.end) if jf else ""
            if used + len(text) > self.max_chars and out:
                dropped += 1
                continue
            used += len(text)
            out.append(ContextSlice(s.file, s.start, s.end, s.role, text))
        if dropped:
            run.note(f"đã cắt {dropped} đoạn mã do trần dung lượng {self.max_chars} ký tự")
        return out
