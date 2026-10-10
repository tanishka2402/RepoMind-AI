"""
Deterministic, evidence-grounded scoring for RepoMind-AI.

Scores are calculated from structured findings and repository evidence.

The LLM does NOT determine numerical repository-health scores.
"""

from typing import Any, Dict, Mapping

from reports.report_schema import (
    CategoryAnalysis,
    RepositoryReport,
)


# ---------------------------------------------------------------------
# Severity penalties
# ---------------------------------------------------------------------
#
# A category starts at 100.
#
# Each finding reduces the score according to its severity.
#
# INFO     -> 0
# LOW      -> 5
# MEDIUM   -> 15
# HIGH     -> 25
# CRITICAL -> 40
#
# The final score is always limited to 0-100.
# ---------------------------------------------------------------------

SEVERITY_PENALTIES = {
    "info": 0,
    "low": 5,
    "medium": 15,
    "high": 25,
    "critical": 40,
}


# ---------------------------------------------------------------------
# Overall repository score weights
# ---------------------------------------------------------------------
#
# Recommendations are intentionally excluded.
#
# They describe actions to take rather than the current repository
# health.
# ---------------------------------------------------------------------

CATEGORY_WEIGHTS = {
    "security": 0.30,
    "risk": 0.20,
    "code_quality": 0.20,
    "architecture": 0.15,
    "documentation": 0.15,
}


def _score_severity(score: int) -> str:
    """
    Convert a numerical score into a risk severity.

    90-100 -> low
    75-89  -> medium
    50-74  -> high
    0-49   -> critical
    """

    if score >= 90:
        return "low"

    if score >= 75:
        return "medium"

    if score >= 50:
        return "high"

    return "critical"


def _evidence_items(
    category: CategoryAnalysis,
) -> list[str]:
    """
    Collect unique evidence from:

    1. category-level evidence
    2. individual finding evidence
    """

    evidence: list[str] = []

    for item in category.evidence:
        if item and item.strip():
            evidence.append(item.strip())

    for finding in category.findings:
        if finding.evidence and finding.evidence.strip():
            evidence.append(
                finding.evidence.strip()
            )

    # Preserve insertion order while removing duplicates.
    return list(dict.fromkeys(evidence))


def _calculate_confidence(
    category: CategoryAnalysis,
    repository_data: Mapping[str, Any],
) -> int:
    """
    Calculate evidence confidence from 0 to 100.

    Confidence measures how strongly the repository evidence supports
    the analysis.

    It is deliberately separate from the health score.

    Score:
        How healthy the category appears.

    Confidence:
        How much concrete repository evidence supports that assessment.
    """

    evidence = _evidence_items(category)

    findings = category.findings

    confidence = 0

    # -------------------------------------------------------------
    # Evidence exists.
    # -------------------------------------------------------------

    if evidence:
        confidence += 40

    # -------------------------------------------------------------
    # Findings contain evidence.
    # -------------------------------------------------------------

    if findings:
        evidenced_findings = sum(
            1
            for finding in findings
            if finding.evidence
            and finding.evidence.strip()
        )

        finding_coverage = (
            evidenced_findings / len(findings)
        )

        confidence += int(
            30 * finding_coverage
        )

    # -------------------------------------------------------------
    # Source-file coverage.
    # -------------------------------------------------------------

    source_files = (
        repository_data.get("source_files")
        or []
    )

    try:
        source_count = len(source_files)
    except TypeError:
        source_count = 0

    source_coverage = min(
        source_count / 10.0,
        1.0,
    )

    confidence += int(
        30 * source_coverage
    )

    return max(
        0,
        min(100, confidence),
    )


def score_category(
    category: CategoryAnalysis,
    repository_data: Mapping[str, Any],
) -> CategoryAnalysis:
    """
    Calculate a deterministic score for one category.
    """

    normalized = category.normalized()

    evidence = _evidence_items(
        normalized
    )

    # -------------------------------------------------------------
    # No evidence:
    #
    # Do not falsely claim that the category is perfect.
    # -------------------------------------------------------------

    if not evidence:
        normalized.score = None
        normalized.severity = "info"
        normalized.confidence = 0

        return normalized

    # -------------------------------------------------------------
    # Calculate severity penalties.
    # -------------------------------------------------------------

    penalty = 0

    for finding in normalized.findings:

        severity = (
            finding.severity
            .lower()
            .strip()
        )

        if severity not in SEVERITY_PENALTIES:
            severity = "info"

        penalty += (
            SEVERITY_PENALTIES[severity]
        )

    # -------------------------------------------------------------
    # Prevent score from going below zero.
    # -------------------------------------------------------------

    penalty = min(
        100,
        penalty,
    )

    score = max(
        0,
        100 - penalty,
    )

    # -------------------------------------------------------------
    # Store deterministic results.
    # -------------------------------------------------------------

    normalized.score = score

    normalized.severity = (
        _score_severity(score)
    )

    normalized.confidence = (
        _calculate_confidence(
            normalized,
            repository_data,
        )
    )

    return normalized


def score_repository_analysis(
    report: RepositoryReport,
    repository_data: Mapping[str, Any],
) -> RepositoryReport:
    """
    Apply deterministic scoring to the complete repository analysis.
    """

    report.architecture = score_category(
        report.architecture,
        repository_data,
    )

    report.code_quality = score_category(
        report.code_quality,
        repository_data,
    )

    report.documentation = score_category(
        report.documentation,
        repository_data,
    )

    report.security = score_category(
        report.security,
        repository_data,
    )

    report.risk = score_category(
        report.risk,
        repository_data,
    )

    # -------------------------------------------------------------
    # Recommendations are not a health category.
    # -------------------------------------------------------------

    report.recommendations.score = None
    report.recommendations.severity = "info"
    report.recommendations.confidence = 0

    return report


def calculate_overall_from_categories(
    categories: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Calculate the overall repository health score.

    Only categories with an actual numerical score are included.

    This means that unavailable categories do not automatically
    become a fake score of 100.
    """

    weighted_score = 0.0
    total_weight = 0.0

    weighted_confidence = 0.0
    confidence_weight = 0.0

    for category_name, weight in CATEGORY_WEIGHTS.items():

        category = categories.get(
            category_name
        )

        if not isinstance(
            category,
            Mapping,
        ):
            continue

        score = category.get(
            "score"
        )

        confidence = category.get(
            "confidence"
        )

        # ---------------------------------------------------------
        # Score
        # ---------------------------------------------------------

        if isinstance(
            score,
            (int, float),
        ):
            weighted_score += (
                float(score) * weight
            )

            total_weight += weight

        # ---------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------

        if isinstance(
            confidence,
            (int, float),
        ):
            weighted_confidence += (
                float(confidence) * weight
            )

            confidence_weight += weight

    # -------------------------------------------------------------
    # No scored categories.
    # -------------------------------------------------------------

    if total_weight == 0:

        return {
            "score": None,
            "severity": "info",
            "confidence": 0,
        }

    # -------------------------------------------------------------
    # Weighted overall score.
    # -------------------------------------------------------------

    overall_score = round(
        weighted_score / total_weight
    )

    # -------------------------------------------------------------
    # Weighted evidence confidence.
    # -------------------------------------------------------------

    if confidence_weight:
        overall_confidence = round(
            weighted_confidence
            / confidence_weight
        )
    else:
        overall_confidence = 0

    return {
        "score": overall_score,
        "severity": _score_severity(
            overall_score
        ),
        "confidence": overall_confidence,
    }


def calculate_overall_from_report(
    report: RepositoryReport,
) -> Dict[str, Any]:
    """
    Calculate the overall score directly from a RepositoryReport.
    """

    categories = {
        "architecture": (
            report.architecture.to_dict()
        ),

        "code_quality": (
            report.code_quality.to_dict()
        ),

        "documentation": (
            report.documentation.to_dict()
        ),

        "security": (
            report.security.to_dict()
        ),

        "risk": (
            report.risk.to_dict()
        ),
    }

    return calculate_overall_from_categories(
        categories
    )