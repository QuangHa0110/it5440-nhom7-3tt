from dataclasses import replace
from pathlib import Path

import pytest

from pr_triage.context import DataflowProvider, load_catalog
from pr_triage.core.models import Variant
from tests.factories import make_finding
from tests.helpers import FIXTURE, REPO_ROOT

CATALOG = load_catalog(REPO_ROOT / "configs" / "context" / "java.yml")


def provider(**kw: int) -> DataflowProvider:
    return DataflowProvider(CATALOG, **kw)


def dao_finding(line: int = 10):  # type: ignore[no-untyped-def]
    return replace(
        make_finding(path="src/app/OrderDao.java", line=line, symbol="OrderDao.find"), cwe="CWE-89"
    )


def test_catalog_loads() -> None:
    assert CATALOG.source_kind('request.getParameter("x")') == "request-parameter"
    assert CATALOG.sink_for("CWE-89") is not None and CATALOG.sink_for("CWE-1") is None
    assert CATALOG.looks_like_sanitizer("escapeSql") and not CATALOG.looks_like_sanitizer("compute")


def test_cross_file_flow_found_through_caller() -> None:
    b = provider().extract(dao_finding(), FIXTURE)
    assert b.variant is Variant.C
    assert b.sink is not None and b.sink.startswith("sql-query: src/app/OrderDao.java:10")
    assert b.source is not None and b.source.startswith(
        "request-parameter (src/app/OrderController.java:"
    )
    assert "OrderDao.buildFilter" in b.sanitizers
    files = {s.file for s in b.slices}
    assert files == {"src/app/OrderDao.java", "src/app/OrderController.java"}
    roles = {s.role for s in b.slices}
    assert "sink-function" in roles
    assert b.slices[0].role == "sink-function"


def test_direct_flow_in_same_function() -> None:
    f = replace(
        make_finding(path="src/app/OrderController.java", line=15, symbol="x"), cwe="CWE-89"
    )
    b = provider().extract(f, FIXTURE)
    assert b.source is not None and "OrderController.java:14" in b.source
    assert not any("không xác định" in m for m in b.missing)


def test_same_input_same_hash() -> None:
    a = provider().extract(dao_finding(), FIXTURE)
    assert a.bundle_hash == provider().extract(dao_finding(), FIXTURE).bundle_hash


def test_hop_limit_reports_missing() -> None:
    b = provider(max_hops=0).extract(dao_finding(), FIXTURE)
    assert b.source is None
    assert any("giới hạn" in m for m in b.missing) and any(
        "nguồn dữ liệu chưa xác định" in m for m in b.missing
    )


def test_size_cap_drops_low_priority_and_records() -> None:
    b = provider(max_chars=250).extract(dao_finding(), FIXTURE)
    assert b.slices[0].role == "sink-function"
    assert any("trần dung lượng" in m for m in b.missing)


def test_no_enclosing_method_falls_back() -> None:
    f = replace(make_finding(path="src/app/OrderDao.java", line=1, symbol=None), cwe="CWE-89")
    b = provider().extract(f, FIXTURE)
    assert b.variant is Variant.C and b.slices[0].role == "alert-site"
    assert any("hàm bao quanh" in m for m in b.missing)


def test_caller_chosen_by_name_and_arity_with_ambiguity_note(tmp_path: Path) -> None:
    (tmp_path / "A.java").write_text(
        "class A {\n"
        "  void run(String p, java.sql.Statement s) throws Exception {\n"
        '    s.executeQuery("x" + p);\n'
        "  }\n}\n"
        "class B {\n"
        "  void go(A a, javax.servlet.http.HttpServletRequest r, java.sql.Statement s)\n"
        "      throws Exception {\n"
        '    a.run(r.getParameter("q"), s);\n'
        "  }\n}\n"
        "class C {\n"
        "  void go(A a, java.sql.Statement s) throws Exception {\n"
        '    a.run("const", s);\n'
        "  }\n}\n"
    )
    f = replace(make_finding(path="A.java", line=3, symbol="A.run"), cwe="CWE-89")
    b = provider().extract(f, tmp_path)
    assert b.source is not None and "request-parameter" in b.source
    assert {s.role for s in b.slices} >= {"sink-function", "caller"}


@pytest.mark.parametrize("hops", [0, 1, 2])
def test_never_raises_on_hops(hops: int) -> None:
    provider(max_hops=hops).extract(dao_finding(), FIXTURE)


def test_servlet_entry_point_has_no_caller_noise_and_receiver_is_traced(tmp_path: Path) -> None:
    (tmp_path / "T.java").write_text(
        "class T {\n"
        "  public void doGet(javax.servlet.http.HttpServletRequest request,\n"
        "      javax.servlet.http.HttpServletResponse response) throws Exception {\n"
        '    String p = request.getHeader("X");\n'
        '    String sql = "{call " + p + "}";\n'
        "    java.sql.CallableStatement st = conn.prepareCall(sql);\n"
        "    st.executeQuery();\n"
        "  }\n}\n"
    )
    f = replace(make_finding(path="T.java", line=7, symbol="T.doGet"), cwe="CWE-89")
    b = provider().extract(f, tmp_path)
    assert b.source is not None and "request-header" in b.source
    assert not any("nơi gọi" in m for m in b.missing)


def test_weak_crypto_is_marked_not_applicable_without_guessing(tmp_path: Path) -> None:
    """ADR 0015 D6: CWE không có luồng dữ liệu thì C ghi rõ không áp dụng, không đoán sink."""
    (tmp_path / "K.java").write_text(
        "class K {\n"
        "  byte[] enc(byte[] data, java.security.Key key) throws Exception {\n"
        '    javax.crypto.Cipher c = javax.crypto.Cipher.getInstance("DES");\n'
        "    c.init(1, key);\n"
        "    return c.doFinal(data);\n"
        "  }\n}\n"
    )
    f = replace(make_finding(path="K.java", line=3, symbol="K.enc"), cwe="CWE-327")
    b = provider().extract(f, tmp_path)
    assert b.sink is None and b.source is None
    assert any("không áp dụng luồng dữ liệu" in m and "CWE-327" in m for m in b.missing)
    assert [s.role for s in b.slices] == ["sink-function"]


def test_catalog_covers_flow_cwes_of_registry_ruleset() -> None:
    for cwe in ("CWE-611", "CWE-502", "CWE-94", "CWE-918", "CWE-601", "CWE-23"):
        assert CATALOG.sink_for(cwe) is not None, cwe
    assert CATALOG.no_dataflow("CWE-319") and CATALOG.no_dataflow("CWE-327")
    assert not CATALOG.no_dataflow("CWE-89") and not CATALOG.no_dataflow(None)


def test_deserialization_sink_traces_back_to_request_body(tmp_path: Path) -> None:
    (tmp_path / "D.java").write_text(
        "class D {\n"
        "  public void doPost(javax.servlet.http.HttpServletRequest request,\n"
        "      javax.servlet.http.HttpServletResponse response) throws Exception {\n"
        "    java.io.ObjectInputStream in =\n"
        "        new java.io.ObjectInputStream(request.getInputStream());\n"
        "    Object o = in.readObject();\n"
        "  }\n}\n"
    )
    f = replace(make_finding(path="D.java", line=6, symbol="D.doPost"), cwe="CWE-502")
    b = provider().extract(f, tmp_path)
    assert b.sink is not None and b.sink.startswith("deserialization: D.java:6 readObject")
    assert b.source is not None and "request-body" in b.source
