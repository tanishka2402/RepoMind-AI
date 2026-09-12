import re


SEVERITY_POINTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
    "info": 0,
}


def calculate_risk_score(report_text: str) -> dict:
    """Calculate a deterministic risk score from report severities."""

    text = str(report_text)

    severities = re.findall(
        r"SEVERITY\s*:\s*(critical|high|medium|low|info)",
        text,
        flags=re.IGNORECASE,
    )

    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    for severity in severities:
        counts[severity.lower()] += 1

    score = sum(
        SEVERITY_POINTS[level] * count
        for level, count in counts.items()
    )

    score = min(score, 100)

    if score >= 75:
        rating = "CRITICAL"
    elif score >= 50:
        rating = "HIGH"
    elif score >= 25:
        rating = "MEDIUM"
    elif score > 0:
        rating = "LOW"
    else:
        rating = "MINIMAL"

    return {
        "score": score,
        "rating": rating,
        "severity_counts": counts,
        "findings_detected": len(severities),
    }
