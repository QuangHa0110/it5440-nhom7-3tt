from pr_triage.core.ports import ContextPort, LlmPort, ScannerPort, ScmPort, StorePort
from pr_triage.store import SqlStore
from tests.fakes import FakeContext, FakeLlm, FakeScanner, FakeScm


def test_fakes_satisfy_ports() -> None:
    scanner: ScannerPort = FakeScanner([])
    ctx: ContextPort = FakeContext()
    llm: LlmPort = FakeLlm()
    scm: ScmPort = FakeScm()
    store: StorePort = SqlStore(":memory:")
    assert (scanner.name, ctx.variant.value) == ("fake", "B")
    assert llm is not None and scm is not None and store is not None
