"""
RepoMind-AI Insight Processing

Converts the grounded repository report into structured
dashboard insights for the frontend.
"""

import re
from typing import Any, Dict, List


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(report: str) -> Dict[str, str]:
    """
    Extract Markdown-style sections from the generated report.

    Example:

    ## Security
    some content

    ## Risk
    some content
    """

    sections: Dict[str, str] = {}

    if not report:
        return sections

    pattern = re.compile(
        r"^#{1,3}\s*(.+?)\s*$",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(report))

    for index, match in enumerate(matches):

        title = match.group(1).strip()

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(report)

        content = report[start:end].strip()

        normalized_title = normalize_title(title)

        sections[normalized_title] = content

    return sections


def normalize_title(title: str) -> str:
    """
    Normalize section titles so slightly different headings
    can still be detected.
    """

    title = title.lower().strip()

    title = re.sub(
        r"[^a-z0-9\s]",
        "",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title


# ============================================================
# SECTION LOOKUP
# ============================================================

def find_section(
    sections: Dict[str, str],
    names: List[str],
) -> str:
    """
    Find the first matching section.
    """

    for name in names:

        normalized = normalize_title(name)

        if normalized in sections:
            return sections[normalized]

    # Fuzzy matching
    for section_name, content in sections.items():

        for name in names:

            normalized = normalize_title(name)

            if (
                normalized in section_name
                or section_name in normalized
            ):
                return content

    return ""


# ============================================================
# KEYWORD ANALYSIS
# ============================================================

def count_keywords(
    text: str,
    keywords: List[str],
) -> int:
    """
    Count occurrences of relevant keywords.
    """

    if not text:
        return 0

    lower_text = text.lower()

    return sum(
        lower_text.count(keyword.lower())
        for keyword in keywords
    )


def determine_status(
    text: str,
    positive_keywords: List[str],
    negative_keywords: List[str],
) -> str:
    """
    Determine a simple insight status.

    PASS:
        positive evidence dominates.

    WARNING:
        insufficient or mixed evidence.

    ATTENTION:
        negative evidence dominates.
    """

    positive = count_keywords(
        text,
        positive_keywords,
    )

    negative = count_keywords(
        text,
        negative_keywords,
    )

    if negative >= positive + 2:
        return "ATTENTION"

    if positive > negative:
        return "GOOD"

    return "WARNING"


# ============================================================
# SCORE
# ============================================================

def calculate_score(
    text: str,
    negative_keywords: List[str],
    positive_keywords: List[str],
) -> int:
    """
    Calculate a deterministic 0-100 insight score.

    The score is deliberately simple and explainable.
    """

    if not text:
        return 50

    negative = count_keywords(
        text,
        negative_keywords,
    )

    positive = count_keywords(
        text,
        positive_keywords,
    )

    score = 70

    score += min(
        positive * 5,
        20,
    )

    score -= min(
        negative * 8,
        50,
    )

    return max(
        0,
        min(
            100,
            score,
        ),
    )


# ============================================================
# SECURITY
# ============================================================

def build_security_insight(
    report: str,
) -> Dict[str, Any]:

    sections = extract_sections(report)

    text = find_section(
        sections,
        [
            "Security",
            "Security Analysis",
            "Security Findings",
        ],
    )

    score = calculate_score(
        text,
        negative_keywords=[
            "vulnerability",
            "vulnerabilities",
            "secret",
            "credential",
            "unsafe",
            "injection",
            "exposed",
            "security issue",
        ],
        positive_keywords=[
            "secure",
            "protected",
            "validated",
            "authentication",
            "authorization",
        ],
    )

    status = determine_status(
        text,
        positive_keywords=[
            "secure",
            "protected",
            "validated",
        ],
        negative_keywords=[
            "vulnerability",
            "secret",
            "credential",
            "unsafe",
            "exposed",
        ],
    )

    return {
        "name": "Security",
        "score": score,
        "status": status,
        "summary": (
            text[:500]
            if text
            else "No dedicated security section was found."
        ),
    }


# ============================================================
# RISK
# ============================================================

def build_risk_insight(
    report: str,
) -> Dict[str, Any]:

    sections = extract_sections(report)

    text = find_section(
        sections,
        [
            "Risk",
            "Risk Analysis",
            "Risk Assessment",
            "Repository Risk",
        ],
    )

    score = calculate_score(
        text,
        negative_keywords=[
            "high risk",
            "critical",
            "severe",
            "major risk",
            "blocker",
            "vulnerability",
        ],
        positive_keywords=[
            "low risk",
            "stable",
            "manageable",
            "controlled",
            "minimal risk",
        ],
    )

    status = determine_status(
        text,
        positive_keywords=[
            "low risk",
            "stable",
            "controlled",
        ],
        negative_keywords=[
            "high risk",
            "critical",
            "severe",
            "blocker",
        ],
    )

    return {
        "name": "Risk",
        "score": score,
        "status": status,
        "summary": (
            text[:500]
            if text
            else "No dedicated risk section was found."
        ),
    }


# ============================================================
# CODE QUALITY
# ============================================================

def build_code_quality_insight(
    report: str,
) -> Dict[str, Any]:

    sections = extract_sections(report)

    text = find_section(
        sections,
        [
            "Code Quality",
            "Code Quality Analysis",
            "Quality",
            "Code Analysis",
        ],
    )

    score = calculate_score(
        text,
        negative_keywords=[
            "bug",
            "issue",
            "duplicate",
            "complex",
            "technical debt",
            "poor quality",
            "code smell",
        ],
        positive_keywords=[
            "clean",
            "maintainable",
            "readable",
            "modular",
            "tested",
            "quality",
        ],
    )

    status = determine_status(
        text,
        positive_keywords=[
            "clean",
            "maintainable",
            "readable",
            "modular",
            "tested",
        ],
        negative_keywords=[
            "bug",
            "duplicate",
            "complex",
            "technical debt",
            "code smell",
        ],
    )

    return {
        "name": "Code Quality",
        "score": score,
        "status": status,
        "summary": (
            text[:500]
            if text
            else "No dedicated code-quality section was found."
        ),
    }


# ============================================================
# ARCHITECTURE
# ============================================================

def build_architecture_insight(
    report: str,
) -> Dict[str, Any]:

    sections = extract_sections(report)

    text = find_section(
        sections,
        [
            "Architecture",
            "Architecture Analysis",
            "Repository Architecture",
        ],
    )

    score = calculate_score(
        text,
        negative_keywords=[
            "tightly coupled",
            "monolithic",
            "complex dependency",
            "architectural issue",
            "poor separation",
        ],
        positive_keywords=[
            "modular",
            "layered",
            "separation",
            "component",
            "scalable",
            "structured",
        ],
    )

    status = determine_status(
        text,
        positive_keywords=[
            "modular",
            "layered",
            "separation",
            "scalable",
            "structured",
        ],
        negative_keywords=[
            "tightly coupled",
            "monolithic",
            "architectural issue",
        ],
    )

    return {
        "name": "Architecture",
        "score": score,
        "status": status,
        "summary": (
            text[:500]
            if text
            else "No dedicated architecture section was found."
        ),
    }


# ============================================================
# DOCUMENTATION
# ============================================================

def build_documentation_insight(
    report: str,
) -> Dict[str, Any]:

    sections = extract_sections(report)

    text = find_section(
        sections,
        [
            "Documentation",
            "Documentation Analysis",
            "Documentation Quality",
        ],
    )

    score = calculate_score(
        text,
        negative_keywords=[
            "missing documentation",
            "undocumented",
            "missing readme",
            "poor documentation",
        ],
        positive_keywords=[
            "documented",
            "documentation",
            "readme",
            "clear",
            "explained",
            "well documented",
        ],
    )

    status = determine_status(
        text,
        positive_keywords=[
            "documented",
            "readme",
            "clear",
            "explained",
        ],
        negative_keywords=[
            "missing documentation",
            "undocumented",
            "poor documentation",
        ],
    )

    return {
        "name": "Documentation",
        "score": score,
        "status": status,
        "summary": (
            text[:500]
            if text
            else "No dedicated documentation section was found."
        ),
    }


# ============================================================
# COMPLETE INSIGHT REPORT
# ============================================================

def build_insights(
    report: str,
) -> Dict[str, Any]:
    """
    Build all dashboard insight cards.
    """

    insights = [
        build_security_insight(report),
        build_risk_insight(report),
        build_code_quality_insight(report),
        build_architecture_insight(report),
        build_documentation_insight(report),
    ]

    scores = [
        insight["score"]
        for insight in insights
    ]

    overall_score = round(
        sum(scores) / len(scores)
    ) if scores else 0

    return {
        "overall_score": overall_score,
        "insights": insights,
    }