"""Chỉ mục ký hiệu bằng tree-sitter-java: hàm bao quanh, thân hàm, lời gọi (ADR 0005).

Ý tưởng dựng ngữ cảnh tất định bằng tree-sitter lấy từ sift-sast (Apache-2.0).
Không sao chép mã.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tree_sitter_java
from tree_sitter import Language, Node, Parser

_LANG = Language(tree_sitter_java.language())
_METHOD_KINDS = {"method_declaration", "constructor_declaration"}
_TYPE_KINDS = {
    "class_declaration",
    "interface_declaration",
    "enum_declaration",
    "record_declaration",
}


@dataclass(frozen=True)
class Method:
    qualified: str
    name: str
    file: str
    start: int
    end: int
    params: tuple[str, ...]


def _text(node: Node | None, src: bytes) -> str:
    return src[node.start_byte : node.end_byte].decode("utf-8", "replace") if node else ""


class JavaFile:
    def __init__(self, rel_path: str, source: bytes) -> None:
        self.rel_path = rel_path
        self.source = source
        self.tree = Parser(_LANG).parse(source)

    def _type_chain(self, node: Node) -> list[str]:
        names: list[str] = []
        cur: Node | None = node.parent
        while cur is not None:
            if cur.type in _TYPE_KINDS:
                names.append(_text(cur.child_by_field_name("name"), self.source))
            cur = cur.parent
        return list(reversed(names))

    def _method_of(self, node: Node) -> Method:
        name = _text(node.child_by_field_name("name"), self.source)
        params_node = node.child_by_field_name("parameters")
        params: list[str] = []
        if params_node is not None:
            for p in params_node.named_children:
                if p.type in ("formal_parameter", "spread_parameter"):
                    params.append(_text(p.child_by_field_name("name"), self.source))
        qualified = ".".join([*self._type_chain(node), name])
        return Method(
            qualified,
            name,
            self.rel_path,
            node.start_point[0] + 1,
            node.end_point[0] + 1,
            tuple(params),
        )

    def methods(self) -> list[Method]:
        out: list[Method] = []
        stack = [self.tree.root_node]
        while stack:
            n = stack.pop()
            if n.type in _METHOD_KINDS:
                out.append(self._method_of(n))
            stack.extend(n.children)
        return sorted(out, key=lambda m: m.start)

    def enclosing_method(self, line: int) -> Method | None:
        """Hàm nhỏ nhất chứa dòng `line` (đánh số từ 1)."""
        point = (line - 1, 0)
        node = self.tree.root_node.descendant_for_point_range(point, point)
        while node is not None and node.type not in _METHOD_KINDS:
            node = node.parent
        return self._method_of(node) if node is not None else None


class SymbolIndex:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._cache: dict[str, JavaFile | None] = {}

    def file(self, rel_path: str) -> JavaFile | None:
        if rel_path not in self._cache:
            path = self._root / rel_path
            self._cache[rel_path] = (
                JavaFile(rel_path, path.read_bytes())
                if path.suffix == ".java" and path.exists()
                else None
            )
        return self._cache[rel_path]

    def enclosing_symbol(self, rel_path: str, line: int) -> str | None:
        f = self.file(rel_path)
        m = f.enclosing_method(line) if f else None
        return m.qualified if m else None
