from export_validator_issue_dashboard import aggregate, metadata_from_body, normalize_issue
from github_validator_issues import build_issue, issue_fingerprint


def test_issue_fingerprint_is_stable():
    record = {
        "path": "chapter/notes/topic.tex",
        "line": 12,
        "severity": "error",
        "code": "toolkit_missing_table",
        "message": "Toolkit box must use a table.",
    }

    assert issue_fingerprint("wsollers/lra-volume-i", "i", record) == issue_fingerprint("wsollers/lra-volume-i", "i", dict(record))


def test_build_issue_embeds_dashboard_metadata():
    report = {"volume_root": "F:/repos/lra-volume-i/volume-i", "records": []}
    record = {
        "path": "book-sets/proofs/topic/prf-example.tex",
        "line": 5,
        "severity": "warning",
        "code": "proof_file_missing_return",
        "message": "Missing return link.",
    }

    issue = build_issue(report, "wsollers/lra-volume-i", record, "https://example.test/run", "abc123")
    metadata = metadata_from_body(issue.body)

    assert metadata["volume"] == "i"
    assert metadata["code"] == "proof_file_missing_return"
    assert metadata["proof_related"] is True
    assert "lra-proof" in issue.labels


def test_dashboard_aggregate_counts_issue_dimensions():
    issues = [
        {"repo": "r1", "volume": "i", "severity": "error", "code": "a", "proof_related": False},
        {"repo": "r1", "volume": "i", "severity": "warning", "code": "b", "proof_related": True},
        {"repo": "r2", "volume": "ii", "severity": "error", "code": "a", "proof_related": True},
    ]

    totals = aggregate(issues)

    assert totals["issue_count"] == 3
    assert totals["proof_issue_count"] == 2
    assert totals["by_severity"] == {"error": 2, "warning": 1}
    assert totals["by_code"] == {"a": 2, "b": 1}


def test_normalize_issue_falls_back_to_labels_when_metadata_is_missing():
    issue = {
        "number": 7,
        "title": "validator issue",
        "state": "open",
        "html_url": "https://example.test/7",
        "labels": [{"name": "lra-validator"}, {"name": "severity:error"}, {"name": "validator:x"}, {"name": "volume:iii"}],
    }

    normalized = normalize_issue("wsollers/lra-volume-iii", issue)

    assert normalized["repo"] == "wsollers/lra-volume-iii"
    assert normalized["severity"] == "error"
    assert normalized["code"] == "x"
    assert normalized["volume"] == "iii"
