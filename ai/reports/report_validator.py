import re
from typing import List


def _extract_evidence_lines(text: str) -> List[str]:
    """
    Extract evidence statements from both plain-text and
    common Markdown formatting produced by the local LLM.

    Supported examples:

    EVIDENCE: index.html contains a stylesheet reference.

    **EVIDENCE:** index.html contains a stylesheet reference.

    ##### Evidence
    index.html contains a stylesheet reference.
    """

    lines = []
    collecting_markdown_evidence = False

    for raw_line in str(text).splitlines():
        stripped = raw_line.strip()

        if not stripped:
            continue

        # ---------------------------------------------------------
        # Plain or Markdown-formatted EVIDENCE:
        # ---------------------------------------------------------

        match = re.match(
            r"^(?:[*_#\s-]*)(?:EVIDENCE|Evidence)\s*:\s*(.*)$",
            stripped,
            flags=re.IGNORECASE,
        )

        if match:
            evidence_text = match.group(1).strip()

            if evidence_text:
                lines.append(
                    f"EVIDENCE: {evidence_text}"
                )

            collecting_markdown_evidence = False
            continue

        # ---------------------------------------------------------
        # Markdown heading:
        #
        # ##### Evidence
        # ---------------------------------------------------------

        markdown_heading = re.match(
            r"^#{1,6}\s*(?:\*\*)?\s*EVIDENCE\s*(?:\*\*)?\s*$",
            stripped,
            flags=re.IGNORECASE,
        )

        if markdown_heading:
            collecting_markdown_evidence = True
            continue

        # ---------------------------------------------------------
        # Stop collecting Markdown evidence when another
        # Markdown heading begins.
        # ---------------------------------------------------------

        if collecting_markdown_evidence and stripped.startswith("#"):
            collecting_markdown_evidence = False

        # ---------------------------------------------------------
        # Collect the line following a Markdown Evidence heading.
        # ---------------------------------------------------------

        if collecting_markdown_evidence:
            lines.append(
                f"EVIDENCE: {stripped}"
            )

    return lines


def validate_report(report_text: str, repository_context: str) -> dict:
    """Validate report evidence against the supplied repository context."""

    evidence_lines = _extract_evidence_lines(report_text)
    context_text = str(repository_context)
    repository_files = {
        match.group(1).strip()
        for match in re.finditer(r"^FILE:\s*(.+)$", context_text, flags=re.MULTILINE)
    }

    evidence_with_file_paths = []
    unsupported_evidence = []
    for evidence in evidence_lines:
        file_paths = re.findall(
            r"(?:^|\s)([\w./-]+\.[\w]+)(?:\s|$|[^\w./-])",
            evidence,
        )
        evidence_with_file_paths.extend(file_paths)
        if file_paths and not any(path in repository_files for path in file_paths):
            unsupported_evidence.append(evidence)

    technology_terms = re.findall(
        r"\b(?:javascript|typescript|python|react|vue|angular|django|flask|node(?:\.js)?)\b",
        str(report_text),
        flags=re.IGNORECASE,
    )
    unsupported_terms = sorted({
        term.lower()
        for term in technology_terms
        if term.lower() not in context_text.lower()
    })

    warnings = []
    if not evidence_lines:
        warnings.append("No evidence statements were found in the report.")
    if unsupported_evidence:
        warnings.append(
            "Some evidence statements reference files not found in the repository context."
        )
    if unsupported_terms:
        warnings.append(
            "Some technology terms were not found in the repository context."
        )

    status = "PASS" if (
        evidence_lines
        and not unsupported_evidence
        and not unsupported_terms
    ) else "WARNING"

    return {
        "status": status,
        "evidence_count": len(evidence_lines),
        "repository_files": sorted(repository_files),
        "warnings": warnings,
        "unsupported_evidence_count": len(unsupported_evidence),
        "evidence_with_file_paths": sorted(set(evidence_with_file_paths)),
        "unsupported_terms": unsupported_terms,
    }


def build_grounding_notice(validation: dict) -> str:
    """Format grounding validation details for inclusion in reports."""

    lines = [
        "GROUNDING VALIDATION",
        f"STATUS: {validation.get('status', 'WARNING')}",
        f"EVIDENCE STATEMENTS: {validation.get('evidence_count', 0)}",
        "",
    ]

    warnings = validation.get("warnings", [])
    if warnings:
        lines.append("WARNINGS:")
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("WARNINGS: None")

    return "\n".join(lines)
