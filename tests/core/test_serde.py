from pr_triage.core.models import ContextBundle, Finding, PrRun, Verdict
from pr_triage.core.serde import from_json, to_json
from tests.factories import make_bundle, make_finding, make_run, make_verdict


def test_roundtrip_all_entities() -> None:
    f = make_finding()
    for obj in (f, make_bundle(f), make_verdict(f), make_run()):
        assert from_json(type(obj), to_json(obj)) == obj


def test_enums_and_tuples_restored() -> None:
    f = make_finding()
    got = from_json(Verdict, to_json(make_verdict(f)))
    assert got.evidence[0].line == 42
    assert isinstance(got.evidence, tuple)
    assert from_json(PrRun, to_json(make_run())).mode.value == "shadow"
    assert isinstance(from_json(Finding, to_json(f)).tools, tuple)
    assert isinstance(from_json(ContextBundle, to_json(make_bundle(f))).slices, tuple)
