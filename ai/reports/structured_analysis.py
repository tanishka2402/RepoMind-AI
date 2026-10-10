"""
RepoMind-AI Structured Analysis Builder.

This module converts the AI workflow output and repository evidence
into the canonical RepositoryReport structure.

Important design principle:

AI output is treated as untrusted input.

Only structured findings with actual evidence are accepted.
When AI output cannot be reliably structured, the system falls back
to conservative repository-grounded information instead of inventing
scores or findings.
"""

import re
from typing import Any, Dict, List, Optional

from reports.report_schema import (
    CategoryAnalysis,
    Finding,
    RepositoryReport,
)


CATEGORY_ALIASES = {
    "architecture": "architecture",
    "architecture findings": "architecture",

    "code quality": "code_quality",
    "code quality findings": "code_quality",

    "documentation": "documentation",
    "documentation findings": "documentation",

    "security": "security",
    "security findings": "security",

    "risk": "risk",
    "risk assessment": "risk",

    "recommendations": "recommendations",
}


SEVERITY_ORDER = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_severity(value: str) -> str:
    value = _clean(value).lower()

    aliases = {
        "informational": "info",
        "notice": "info",
        "moderate": "medium",
        "severe": "high",
        "critical": "critical",
    }

    value = aliases.get(value, value)

    if value not in SEVERITY_ORDER:
        return "info"

    return value


def _extract_field(
    block: str,
    field_name: str,
) -> str:
    """
    Extract a simple REPORT FIELD: value entry.
    """

    pattern = rf"(?im)^\s*{re.escape(field_name)}\s*:\s*(.+?)\s*$"

    match = re.search(pattern, block)

    if not match:
        return ""

    return match.group(1).strip()


def _extract_category_blocks(
    report_text: str,
) -> Dict[str, str]:
    """
    Split the raw AI report into category blocks.

    This parser intentionally supports the format already produced by
    the deterministic report builder.
    """

    lines = report_text.splitlines()

    blocks: Dict[str, List[str]] = {}

    current_category: Optional[str] = None

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.upper() in {
            "ARCHITECTURE FINDINGS",
            "CODE QUALITY FINDINGS",
            "DOCUMENTATION FINDINGS",
            "SECURITY FINDINGS",
            "RISK ASSESSMENT",
            "RECOMMENDATIONS",
        }:
            normalized = stripped.lower()
            current_category = CATEGORY_ALIASES.get(
                normalized
            )

            if current_category:
                blocks.setdefault(
                    current_category,
                    [],
                )

            continue

        category_match = re.match(
            r"(?i)^CATEGORY\s*:\s*(.+)$",
            stripped,
        )

        if category_match:
            category_name = (
                category_match.group(1)
                .strip()
                .lower()
            )

            current_category = CATEGORY_ALIASES.get(
                category_name
            )

            if current_category:
                blocks.setdefault(
                    current_category,
                    [],
                )

            continue

        if current_category:
            blocks[current_category].append(line)

    return {
        key: "\n".join(value)
        for key, value in blocks.items()
    }


def _build_findings_from_block(
    category: str,
    block: str,
) -> List[Finding]:
    """
    Convert repeated structured fields into findings.

    The current deterministic report emits one finding per category.
    This parser is intentionally tolerant so future AI output can emit
    multiple findings.
    """

    if not block.strip():
        return []

    titles = re.findall(
        r"(?im)^\s*TITLE\s*:\s*(.+?)\s*$",
        block,
    )

    descriptions = re.findall(
        r"(?im)^\s*DESCRIPTION\s*:\s*(.+?)\s*$",
        block,
    )

    evidences = re.findall(
        r"(?im)^\s*EVIDENCE\s*:\s*(.+?)\s*$",
        block,
    )

    recommendations = re.findall(
        r"(?im)^\s*RECOMMENDATION\s*:\s*(.+?)\s*$",
        block,
    )

    severities = re.findall(
        r"(?im)^\s*SEVERITY\s*:\s*(.+?)\s*$",
        block,
    )

    count = max(
        len(titles),
        len(descriptions),
        len(evidences),
        len(recommendations),
        len(severities),
    )

    if count == 0:
        return []

    findings: List[Finding] = []

    for index in range(count):
        title = (
            titles[index]
            if index < len(titles)
            else f"{category.title()} observation"
        )

        description = (
            descriptions[index]
            if index < len(descriptions)
            else ""
        )

        evidence = (
            evidences[index]
            if index < len(evidences)
            else ""
        )

        recommendation = (
            recommendations[index]
            if index < len(recommendations)
            else ""
        )

        severity = (
            severities[index]
            if index < len(severities)
            else "info"
        )

        if not (
            title.strip()
            or description.strip()
            or evidence.strip()
        ):
            continue

        findings.append(
            Finding(
                category=category,
                title=title,
                description=description,
                evidence=evidence,
                severity=_normalize_severity(
                    severity
                ),
                recommendation=recommendation,
            )
        )

    return findings


def _category_from_findings(
    findings: List[Finding],
) -> CategoryAnalysis:
    if not findings:
        return CategoryAnalysis()

    highest_severity = max(
        (
            _normalize_severity(
                finding.severity
            )
            for finding in findings
        ),
        key=lambda value: SEVERITY_ORDER[value],
    )

    evidence = [
        finding.evidence
        for finding in findings
        if finding.evidence
    ]

    recommendations = [
        finding.recommendation
        for finding in findings
        if finding.recommendation
    ]

    return CategoryAnalysis(
        score=None,
        severity=highest_severity,
        findings=findings,
        evidence=evidence,
        recommendations=recommendations,
    )


def _grounded_fallback(
    repository_data: Dict[str, Any],
    category: str,
) -> CategoryAnalysis:
    """
    Build a conservative category when AI output is unavailable.

    No fabricated score is produced.
    """

    source_files = repository_data.get(
        "source_files",
        [],
    )

    files = repository_data.get(
        "files",
        [],
    )

    source_count = len(source_files)
    file_count = len(files)

    full_name = (
        repository_data.get("full_name")
        or repository_data.get("name")
        or "Unknown repository"
    )

    if category == "architecture":
        evidence = (
            f"Repository collection returned "
            f"{source_count} source files for {full_name}."
        )

        finding = Finding(
            category="architecture",
            title="Observed source structure",
            description=(
                "Architecture assessment is limited to "
                "the source files collected by the repository "
                "analysis pipeline."
            ),
            evidence=evidence,
            severity="info",
            recommendation=(
                "Use the collected source structure as the "
                "evidence base for deeper architecture review."
            ),
        )

    elif category == "code_quality":
        finding = Finding(
            category="code_quality",
            title="Available code-quality evidence",
            description=(
                "Code-quality assessment is limited to the "
                f"{source_count} collected source files."
            ),
            evidence=(
                f"Repository collection returned "
                f"{source_count} source files."
            ),
            severity="info",
            recommendation=(
                "Perform detailed quality checks only against "
                "source files actually collected."
            ),
        )

    elif category == "documentation":
        markdown_files = [
            item.get("path")
            for item in source_files
            if str(
                item.get("path", "")
            ).lower().endswith(".md")
        ]

        finding = Finding(
            category="documentation",
            title="Documentation coverage",
            description=(
                "Documentation assessment is based on the "
                "documentation files collected by the pipeline."
            ),
            evidence=(
                "Collected Markdown files: "
                + (
                    ", ".join(
                        str(path)
                        for path in markdown_files
                    )
                    if markdown_files
                    else "none"
                )
                + "."
            ),
            severity="info",
            recommendation=(
                "Review project documentation for usage, "
                "maintenance, and contribution guidance."
            ),
        )

    elif category == "security":
        finding = Finding(
            category="security",
            title="Security assessment scope",
            description=(
                "Security assessment is limited to the "
                "repository information and source files "
                "collected by the pipeline."
            ),
            evidence=(
                f"The analysis pipeline collected "
                f"{source_count} source files and "
                f"{file_count} repository files."
            ),
            severity="info",
            recommendation=(
                "Do not interpret the absence of a reported "
                "issue as proof that no vulnerabilities exist."
            ),
        )

    elif category == "risk":
        finding = Finding(
            category="risk",
            title="Repository analysis coverage",
            description=(
                "Risk assessment is limited to the information "
                "collected from the repository."
            ),
            evidence=(
                f"Repository collection returned "
                f"{file_count} files and "
                f"{source_count} source files."
            ),
            severity="info",
            recommendation=(
                "Verify important risks against the repository "
                "and additional engineering evidence."
            ),
        )

    else:
        finding = Finding(
            category="recommendations",
            title="Evidence-based analysis",
            description=(
                "Recommendations should remain tied to "
                "information collected from the repository."
            ),
            evidence=(
                f"The pipeline collected {file_count} files "
                f"and {source_count} source files."
            ),
            severity="info",
            recommendation=(
                "Continue using explicit repository evidence "
                "when producing analysis recommendations."
            ),
        )

    return CategoryAnalysis(
        findings=[finding],
        evidence=[finding.evidence],
        recommendations=[finding.recommendation],
        severity=finding.severity,
    )


def build_structured_analysis(
    repository_data: Dict[str, Any],
    raw_ai_report: str,
) -> RepositoryReport:
    """
    Convert repository + AI output into the canonical structure.

    AI findings are accepted when they can be parsed into the existing
    evidence-oriented format. Missing categories use conservative
    repository-grounded fallbacks.
    """

    full_name = (
        repository_data.get("full_name")
        or repository_data.get("name")
        or "Unknown repository"
    )

    blocks = _extract_category_blocks(
        raw_ai_report or ""
    )

    category_names = [
        "architecture",
        "code_quality",
        "documentation",
        "security",
        "risk",
        "recommendations",
    ]

    category_results: Dict[str, CategoryAnalysis] = {}

    for category in category_names:
        block = blocks.get(category, "")

        findings = _build_findings_from_block(
            category=category,
            block=block,
        )

        if findings:
            category_results[category] = (
                _category_from_findings(findings)
            )
        else:
            category_results[category] = (
                _grounded_fallback(
                    repository_data,
                    category,
                )
            )

    description = _clean(
        repository_data.get("description")
    )

    if description:
        summary = (
            f"{full_name}: {description}"
        )
    else:
        summary = (
            f"{full_name} was analyzed using the "
            "RepoMind-AI repository collection and "
            "multi-agent analysis pipeline."
        )

    return RepositoryReport(
        repository=full_name,
        executive_summary=summary,
        architecture=category_results["architecture"],
        code_quality=category_results["code_quality"],
        documentation=category_results["documentation"],
        security=category_results["security"],
        risk=category_results["risk"],
        recommendations=category_results["recommendations"],
    )
