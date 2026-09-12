"""
RepoMind-AI JSON Report Generator.
"""

import json
from pathlib import Path
from datetime import datetime


def generate_json(
    result,
    repository_name="repository",
    output_dir="reports",
):
    """Generate a structured JSON report."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_text = str(result)

    report = {
        "project": "RepoMind-AI",
        "repository": repository_name,
        "generated_at": datetime.now().isoformat(),
        "status": "completed",
        "analysis": {
            "raw": report_text,
            "sections": {
                "executive_summary": _extract_section(
                    report_text,
                    "EXECUTIVE SUMMARY",
                    "REPOSITORY OVERVIEW",
                ),
                "repository_overview": _extract_section(
                    report_text,
                    "REPOSITORY OVERVIEW",
                    "ARCHITECTURE FINDINGS",
                ),
                "architecture": _extract_section(
                    report_text,
                    "ARCHITECTURE FINDINGS",
                    "CODE QUALITY FINDINGS",
                ),
                "code_quality": _extract_section(
                    report_text,
                    "CODE QUALITY FINDINGS",
                    "DOCUMENTATION FINDINGS",
                ),
                "documentation": _extract_section(
                    report_text,
                    "DOCUMENTATION FINDINGS",
                    "SECURITY FINDINGS",
                ),
                "security": _extract_section(
                    report_text,
                    "SECURITY FINDINGS",
                    "RISK ASSESSMENT",
                ),
                "risks": _extract_section(
                    report_text,
                    "RISK ASSESSMENT",
                    "RECOMMENDATIONS",
                ),
                "recommendations": _extract_section(
                    report_text,
                    "RECOMMENDATIONS",
                    None,
                ),
            },
        },
    }

    file_path = output_path / "repository_analysis.json"

    file_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return file_path


def _extract_section(text, start_heading, end_heading):
    """Extract one section from the AI result."""

    start = text.find(start_heading)

    if start == -1:
        return ""

    start += len(start_heading)

    if end_heading:
        end = text.find(end_heading, start)

        if end == -1:
            return text[start:].strip()

        return text[start:end].strip()

    return text[start:].strip()
