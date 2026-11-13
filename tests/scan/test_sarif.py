import json

from pr_triage.scan import parse_sarif

SARIF = json.dumps(
    {
        "runs": [
            {
                "tool": {
                    "driver": {
                        "rules": [
                            {
                                "id": "a.b.configs.sqli",
                                "properties": {"tags": ["security", "CWE-89: SQL Injection"]},
                                "defaultConfiguration": {"level": "error"},
                            }
                        ]
                    }
                },
                "results": [
                    {
                        "ruleId": "a.b.configs.sqli",
                        "message": {"text": "tainted"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "src/A.java"},
                                    "region": {
                                        "startLine": 5,
                                        "endLine": 6,
                                        "snippet": {"text": "q(x)"},
                                    },
                                }
                            }
                        ],
                        "codeFlows": [
                            {
                                "threadFlows": [
                                    {
                                        "locations": [
                                            {
                                                "location": {
                                                    "message": {"text": "source"},
                                                    "physicalLocation": {
                                                        "artifactLocation": {"uri": "src/A.java"},
                                                        "region": {"startLine": 2},
                                                    },
                                                }
                                            },
                                            {
                                                "location": {
                                                    "message": {"text": "sink"},
                                                    "physicalLocation": {
                                                        "artifactLocation": {"uri": "src/A.java"},
                                                        "region": {"startLine": 5},
                                                    },
                                                }
                                            },
                                        ]
                                    }
                                ]
                            }
                        ],
                    },
                    {"ruleId": "x", "message": {"text": "no location"}, "locations": []},
                ],
            }
        ]
    }
)


def test_parse_fields_and_flow() -> None:
    (f,) = parse_sarif(SARIF, "semgrep", ("sqli",))
    assert (f.rule_id, f.cwe, f.severity) == ("sqli", "CWE-89", "high")
    assert (f.file, f.line_start, f.line_end, f.snippet) == ("src/A.java", 5, 6, "q(x)")
    assert [s.line for s in f.flow] == [2, 5]
    assert f.flow[0].message == "source"


def test_registry_rule_id_kept_when_not_local() -> None:
    (f,) = parse_sarif(SARIF, "semgrep")
    assert f.rule_id == "a.b.configs.sqli"


def test_empty_sarif() -> None:
    assert parse_sarif('{"runs": []}', "semgrep") == []
