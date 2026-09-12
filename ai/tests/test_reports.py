from reports.report_validator import validate_report
from reports.risk_scorer import calculate_risk_score


def test_grounding_passes_for_supported_evidence():
    repository_context = """
REPOSITORY FACTS

SOURCE CODE

FILE: index.html
LANGUAGE: HTML
------------------------------------------------------------
<html>
<body>Hello</body>
</html>
------------------------------------------------------------
"""

    report = """
ARCHITECTURE FINDINGS

EVIDENCE: index.html contains the main HTML document.
SEVERITY: info
"""

    result = validate_report(
        report_text=report,
        repository_context=repository_context,
    )

    assert result["status"] == "PASS"
    assert result["evidence_count"] == 1
    assert result["unsupported_evidence_count"] == 0
    assert "index.html" in result["evidence_with_file_paths"]


def test_grounding_warns_when_evidence_has_unknown_file():
    repository_context = """
SOURCE CODE

FILE: index.html
LANGUAGE: HTML
------------------------------------------------------------
<html></html>
------------------------------------------------------------
"""

    report = """
SECURITY FINDINGS

EVIDENCE: app.js contains an authentication vulnerability.
SEVERITY: high
"""

    result = validate_report(
        report_text=report,
        repository_context=repository_context,
    )

    assert result["status"] == "WARNING"
    assert result["evidence_count"] == 1
    assert result["unsupported_evidence_count"] == 1


def test_grounding_warns_when_no_evidence_exists():
    repository_context = """
SOURCE CODE

FILE: index.html
LANGUAGE: HTML
------------------------------------------------------------
<html></html>
------------------------------------------------------------
"""

    report = """
SECURITY FINDINGS

The application has serious security problems.
"""

    result = validate_report(
        report_text=report,
        repository_context=repository_context,
    )

    assert result["status"] == "WARNING"
    assert result["evidence_count"] == 0


def test_grounding_detects_unsupported_technology():
    repository_context = """
SOURCE CODE

FILE: index.html
LANGUAGE: HTML
------------------------------------------------------------
<html></html>
------------------------------------------------------------
"""

    report = """
CODE QUALITY FINDINGS

The JavaScript implementation should be refactored.
"""

    result = validate_report(
        report_text=report,
        repository_context=repository_context,
    )

    assert result["status"] == "WARNING"
    assert "javascript" in result["unsupported_terms"]


def test_risk_score_for_high_severity_finding():
    report = """
SECURITY FINDINGS

EVIDENCE: index.html contains a security issue.
SEVERITY: high
"""

    result = calculate_risk_score(report)

    assert result["score"] == 15
    assert result["rating"] == "LOW"
    assert result["severity_counts"]["high"] == 1
    assert result["findings_detected"] == 1


def test_risk_score_for_multiple_severities():
    report = """
SEVERITY: critical
SEVERITY: high
SEVERITY: medium
SEVERITY: low
SEVERITY: info
"""

    result = calculate_risk_score(report)

    assert result["score"] == 51
    assert result["rating"] == "HIGH"
    assert result["severity_counts"]["critical"] == 1
    assert result["severity_counts"]["high"] == 1
    assert result["severity_counts"]["medium"] == 1
    assert result["severity_counts"]["low"] == 1
    assert result["severity_counts"]["info"] == 1
    assert result["findings_detected"] == 5


def test_risk_score_is_capped_at_100():
    report = "\n".join(
        ["SEVERITY: critical"] * 10
    )

    result = calculate_risk_score(report)

    assert result["score"] == 100
    assert result["rating"] == "CRITICAL"
    assert result["findings_detected"] == 10
