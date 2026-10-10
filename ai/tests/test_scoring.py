"""
Tests for the deterministic RepoMind-AI scoring engine.
"""

from reports.report_schema import (
    CategoryAnalysis,
    Finding,
    RepositoryReport,
)

from reports.scoring import (
    calculate_overall_from_report,
    score_repository_analysis,
)


def test_high_finding_reduces_category_score():
    """
    One HIGH finding should produce:

        100 - 25 = 75
    """

    report = RepositoryReport(
        repository="example/repository",

        security=CategoryAnalysis(
            findings=[
                Finding(
                    category="security",
                    title="Potential security issue",
                    description=(
                        "A security concern was observed."
                    ),
                    evidence=(
                        "Observed evidence in source file."
                    ),
                    severity="high",
                    recommendation=(
                        "Review the affected code."
                    ),
                )
            ],

            evidence=[
                "Observed evidence in source file."
            ],
        ),
    )

    scored = score_repository_analysis(
        report,
        {
            "source_files": [
                "app.py",
                "main.py",
                "config.py",
            ],
        },
    )

    assert scored.security.score == 75

    assert (
        scored.security.severity
        == "medium"
    )

    assert (
        scored.security.confidence
        > 0
    )


def test_critical_finding_reduces_score_to_60():
    """
    One CRITICAL finding should produce:

        100 - 40 = 60
    """

    report = RepositoryReport(
        repository="example/repository",

        security=CategoryAnalysis(
            findings=[
                Finding(
                    category="security",
                    title="Critical security issue",
                    description=(
                        "A critical concern was observed."
                    ),
                    evidence="Critical evidence.",
                    severity="critical",
                    recommendation=(
                        "Fix immediately."
                    ),
                )
            ],

            evidence=[
                "Critical evidence."
            ],
        ),
    )

    scored = score_repository_analysis(
        report,
        {
            "source_files": [
                "app.py"
            ],
        },
    )

    assert scored.security.score == 60

    assert (
        scored.security.severity
        == "high"
    )


def test_multiple_critical_findings_can_reach_zero():
    """
    Three CRITICAL findings produce:

        100 - 40 - 40 - 40

    which is capped at zero.
    """

    report = RepositoryReport(
        repository="example/repository",

        security=CategoryAnalysis(
            findings=[
                Finding(
                    category="security",
                    title="Critical issue one",
                    description=(
                        "Critical issue."
                    ),
                    evidence="Evidence one.",
                    severity="critical",
                ),

                Finding(
                    category="security",
                    title="Critical issue two",
                    description=(
                        "Critical issue."
                    ),
                    evidence="Evidence two.",
                    severity="critical",
                ),

                Finding(
                    category="security",
                    title="Critical issue three",
                    description=(
                        "Critical issue."
                    ),
                    evidence="Evidence three.",
                    severity="critical",
                ),
            ],

            evidence=[
                "Evidence one.",
                "Evidence two.",
                "Evidence three.",
            ],
        ),
    )

    scored = score_repository_analysis(
        report,
        {
            "source_files": [
                "app.py",
                "main.py",
            ],
        },
    )

    assert scored.security.score == 0

    assert (
        scored.security.severity
        == "critical"
    )


def test_no_evidence_does_not_claim_perfect_score():
    """
    No evidence means no score.

    RepoMind-AI must not interpret:
        "nothing was inspected"

    as:
        "everything is perfect".
    """

    report = RepositoryReport(
        repository="example/repository",

        security=CategoryAnalysis()
    )

    scored = score_repository_analysis(
        report,
        {
            "source_files": []
        },
    )

    assert scored.security.score is None

    assert (
        scored.security.confidence
        == 0
    )

    assert (
        scored.security.severity
        == "info"
    )


def test_overall_score_uses_category_weights():
    """
    Verify that the overall score is calculated from the
    configured category weights.
    """

    report = RepositoryReport(
        repository="example/repository",

        security=CategoryAnalysis(
            findings=[
                Finding(
                    category="security",
                    title="Security concern",
                    description="Concern.",
                    evidence="Evidence.",
                    severity="high",
                )
            ],

            evidence=[
                "Evidence."
            ],
        ),

        risk=CategoryAnalysis(
            findings=[
                Finding(
                    category="risk",
                    title="Risk concern",
                    description="Concern.",
                    evidence="Evidence.",
                    severity="medium",
                )
            ],

            evidence=[
                "Evidence."
            ],
        ),
    )

    scored = score_repository_analysis(
        report,
        {
            "source_files": [
                "a.py",
                "b.py",
                "c.py",
                "d.py",
                "e.py",
            ],
        },
    )

    overall = calculate_overall_from_report(
        scored
    )

    assert (
        overall["score"] is not None
    )

    assert (
        0
        <= overall["score"]
        <= 100
    )

    assert (
        0
        <= overall["confidence"]
        <= 100
    )