from pathlib import Path

from pr_triage.context import SymbolIndex
from tests.helpers import FIXTURE


def test_enclosing_symbol_and_methods() -> None:
    idx = SymbolIndex(FIXTURE)
    assert idx.enclosing_symbol("src/app/OrderDao.java", 10) == "OrderDao.find"
    assert idx.enclosing_symbol("src/app/OrderController.java", 15) == "OrderController.showDirect"
    assert idx.enclosing_symbol("src/app/OrderDao.java", 1) is None
    f = idx.file("src/app/OrderDao.java")
    assert f is not None
    names = [m.qualified for m in f.methods()]
    assert names == ["OrderDao.find", "OrderDao.buildFilter", "OrderDao.safe"]
    assert f.methods()[0].params == ("status",)


def test_missing_and_non_java_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    idx = SymbolIndex(tmp_path)
    assert idx.enclosing_symbol("nope.java", 1) is None
    assert idx.enclosing_symbol("a.txt", 1) is None


def test_nested_class_names(tmp_path: Path) -> None:
    (tmp_path / "A.java").write_text(
        "class A {\n  class B {\n    void m() {\n      int x;\n    }\n  }\n}\n"
    )
    assert SymbolIndex(tmp_path).enclosing_symbol("A.java", 4) == "A.B.m"
