
"""
RepoMind-AI
Main entry point.

Pipeline:

GitHub URL
    ↓
RepositoryFetcher
    ↓
ContextBuilder
    ↓
8 AI Agents
    ↓
AI Analysis
    ↓
Deterministic Grounded Finalization
    ↓
Grounding Validation
    ↓
Markdown + JSON + HTML Reports
"""

import sys
from typing import Any, Dict, List

from github_service.repository_fetcher import RepositoryFetcher
from context.context_builder import ContextBuilder
from workflow.crew import RepoMindCrew

from reports.report_validator import (
    validate_report,
    build_grounding_notice,
)

from reports.markdown_generator import generate_markdown
from reports.json_generator import generate_json
from reports.html_generator import generate_html


# -----------------------------------------------------------------
# Deterministic grounded report builder
# -----------------------------------------------------------------


def build_grounded_report(repository_data: Dict[str, Any]) -> str:
    """
    Build a conservative final report directly from repository data.

    This is intentionally deterministic.

    The local LLM is still used for repository analysis, but malformed
    or unsupported model output must not become the final verified
    repository report.
    """

    name = repository_data.get("name") or "Unknown"
    full_name = repository_data.get("full_name") or name
    description = repository_data.get("description")

    default_branch = repository_data.get(
        "default_branch"
    ) or "Unavailable"

    url = repository_data.get("url") or "Unavailable"

    stars = repository_data.get("stars", 0)
    forks = repository_data.get("forks", 0)
    watchers = repository_data.get("watchers", 0)
    open_issues = repository_data.get("open_issues", 0)

    languages = repository_data.get(
        "languages",
        {},
    )

    files = repository_data.get(
        "files",
        [],
    )

    source_files = repository_data.get(
        "source_files",
        [],
    )

    issues = repository_data.get(
        "issues",
        [],
    )

    pull_requests = repository_data.get(
        "pull_requests",
        [],
    )

    branches = repository_data.get(
        "branches",
        [],
    )

    report_parts: List[str] = []

    # -------------------------------------------------------------
    # Executive Summary
    # -------------------------------------------------------------

    report_parts.append("EXECUTIVE SUMMARY")

    report_parts.append(
        f"The repository analyzed is {full_name}."
    )

    if description:
        report_parts.append(
            f"Repository description: {description}"
        )

    report_parts.append(
        f"The default branch is {default_branch}."
    )

    report_parts.append(
        f"GitHub reports {stars} stars, "
        f"{forks} forks, "
        f"{watchers} watchers, and "
        f"{open_issues} open issues."
    )

    report_parts.append(
        f"The fetcher collected {len(files)} top-level files "
        f"and {len(source_files)} source files for analysis."
    )

    report_parts.append(
        "The findings below are restricted to information "
        "observed by the repository collection pipeline."
    )

    # -------------------------------------------------------------
    # Repository Overview
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("REPOSITORY OVERVIEW")

    report_parts.append(
        f"CATEGORY: Repository"
    )
    report_parts.append(
        f"TITLE: Repository metadata"
    )
    report_parts.append(
        f"SEVERITY: info"
    )
    report_parts.append(
        f"DESCRIPTION: The analyzed repository is {full_name}. "
        f"The default branch is {default_branch}."
    )
    report_parts.append(
        f"EVIDENCE: Repository metadata reports "
        f"full_name={full_name} and "
        f"default_branch={default_branch}."
    )
    report_parts.append(
        f"RECOMMENDATION: Continue reviewing the repository "
        f"using the collected source files and GitHub metadata."
    )

    # -------------------------------------------------------------
    # Language information
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "CATEGORY: Repository"
    )
    report_parts.append(
        "TITLE: Observed repository languages"
    )
    report_parts.append(
        "SEVERITY: info"
    )

    if languages:
        language_names = ", ".join(
            str(language)
            for language in languages.keys()
        )

        report_parts.append(
            f"DESCRIPTION: The GitHub language metadata identifies "
            f"the following observed languages: {language_names}."
        )

        report_parts.append(
            f"EVIDENCE: GitHub language metadata lists "
            f"{language_names}."
        )
    else:
        report_parts.append(
            "DESCRIPTION: No language metadata was returned "
            "by the repository collection pipeline."
        )

        report_parts.append(
            "EVIDENCE: The collected repository language metadata "
            "is empty."
        )

    report_parts.append(
        "RECOMMENDATION: Treat the collected language metadata "
        "as the observed technology information for this report."
    )

    # -------------------------------------------------------------
    # Architecture
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("ARCHITECTURE FINDINGS")

    if source_files:
        source_paths = [
            str(item.get("path"))
            for item in source_files
            if item.get("path")
        ]

        report_parts.append(
            "CATEGORY: Architecture"
        )
        report_parts.append(
            "TITLE: Collected source structure"
        )
        report_parts.append(
            "SEVERITY: info"
        )
        report_parts.append(
            f"DESCRIPTION: The analysis pipeline collected "
            f"{len(source_paths)} source files for direct inspection."
        )
        report_parts.append(
            "EVIDENCE: Collected source files include: "
            + ", ".join(source_paths)
            + "."
        )
        report_parts.append(
            "RECOMMENDATION: Use the collected file paths as the "
            "basis for further architecture analysis."
        )
    else:
        report_parts.append(
            "CATEGORY: Architecture"
        )
        report_parts.append(
            "TITLE: Source coverage"
        )
        report_parts.append(
            "SEVERITY: info"
        )
        report_parts.append(
            "DESCRIPTION: No source files were collected for "
            "direct inspection."
        )
        report_parts.append(
            "EVIDENCE: The repository collection pipeline returned "
            "zero source files."
        )
        report_parts.append(
            "RECOMMENDATION: Review the repository contents directly "
            "if deeper source-level architecture analysis is required."
        )

    # -------------------------------------------------------------
    # Code Quality
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("CODE QUALITY FINDINGS")

    report_parts.append(
        "CATEGORY: Code Quality"
    )
    report_parts.append(
        "TITLE: Available source coverage"
    )
    report_parts.append(
        "SEVERITY: info"
    )
    report_parts.append(
        f"DESCRIPTION: Code-quality observations are limited to "
        f"the {len(source_files)} source files collected by the "
        f"repository fetcher."
    )

    if source_files:
        evidence_paths = [
            str(item.get("path"))
            for item in source_files
            if item.get("path")
        ]

        report_parts.append(
            "EVIDENCE: Source files collected for inspection: "
            + ", ".join(evidence_paths)
            + "."
        )
    else:
        report_parts.append(
            "EVIDENCE: No source files were collected for inspection."
        )

    report_parts.append(
        "RECOMMENDATION: Perform detailed code-quality review "
        "only against source files that are actually collected."
    )

    # -------------------------------------------------------------
    # Documentation
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("DOCUMENTATION FINDINGS")

    documentation_files = [
        str(item.get("path"))
        for item in source_files
        if str(item.get("path", "")).lower().endswith(".md")
    ]

    if documentation_files:
        report_parts.append(
            "CATEGORY: Documentation"
        )
        report_parts.append(
            "TITLE: Markdown documentation"
        )
        report_parts.append(
            "SEVERITY: info"
        )
        report_parts.append(
            "DESCRIPTION: Markdown documentation was collected "
            "from the repository."
        )
        report_parts.append(
            "EVIDENCE: Collected Markdown files: "
            + ", ".join(documentation_files)
            + "."
        )
        report_parts.append(
            "RECOMMENDATION: Review the collected documentation "
            "for project-specific usage and maintenance guidance."
        )
    else:
        report_parts.append(
            "CATEGORY: Documentation"
        )
        report_parts.append(
            "TITLE: Markdown documentation coverage"
        )
        report_parts.append(
            "SEVERITY: info"
        )
        report_parts.append(
            "DESCRIPTION: No Markdown source file was collected "
            "for documentation inspection."
        )
        report_parts.append(
            "EVIDENCE: The collected source-file paths contain "
            "no Markdown file."
        )
        report_parts.append(
            "RECOMMENDATION: Review repository documentation "
            "separately if documentation is required."
        )

    # -------------------------------------------------------------
    # Security
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("SECURITY FINDINGS")

    report_parts.append(
        "CATEGORY: Security"
    )
    report_parts.append(
        "TITLE: Security assessment scope"
    )
    report_parts.append(
        "SEVERITY: info"
    )
    report_parts.append(
        "DESCRIPTION: The available security assessment is "
        "limited to the repository information and source files "
        "collected by the pipeline."
    )

    if source_files:
        security_paths = [
            str(item.get("path"))
            for item in source_files
            if item.get("path")
        ]

        report_parts.append(
            "EVIDENCE: Security review scope includes the "
            "collected files: "
            + ", ".join(security_paths)
            + "."
        )
    else:
        report_parts.append(
            "EVIDENCE: No source files were collected for "
            "security inspection."
        )

    report_parts.append(
        "RECOMMENDATION: Do not interpret the absence of a "
        "reported security issue as proof that the repository "
        "contains no security vulnerabilities."
    )

    # -------------------------------------------------------------
    # Risk Assessment
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("RISK ASSESSMENT")

    report_parts.append(
        "CATEGORY: Analysis Scope"
    )
    report_parts.append(
        "TITLE: Repository analysis coverage"
    )
    report_parts.append(
        "SEVERITY: info"
    )
    report_parts.append(
        f"DESCRIPTION: The final assessment is based on "
        f"{len(files)} collected files and "
        f"{len(source_files)} collected source files."
    )

    report_parts.append(
        "EVIDENCE: Repository collection returned "
        f"{len(files)} files and "
        f"{len(source_files)} source files."
    )

    report_parts.append(
        "RECOMMENDATION: Treat findings outside the collected "
        "repository information as requiring additional verification."
    )

    # -------------------------------------------------------------
    # Recommendations
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append("RECOMMENDATIONS")

    report_parts.append(
        "CATEGORY: Process"
    )
    report_parts.append(
        "TITLE: Maintain evidence-based repository analysis"
    )
    report_parts.append(
        "SEVERITY: info"
    )
    report_parts.append(
        "DESCRIPTION: Repository findings should remain tied "
        "to information collected directly from GitHub."
    )
    report_parts.append(
        "EVIDENCE: The repository analysis pipeline collected "
        f"{len(source_files)} source files and "
        f"{len(files)} repository files."
    )
    report_parts.append(
        "RECOMMENDATION: Continue using explicit repository "
        "evidence when producing analysis findings."
    )

    return "\n".join(report_parts)


# -----------------------------------------------------------------
# Main
# -----------------------------------------------------------------


def main():
    print("=" * 70)
    print("RepoMind-AI")
    print("AI REPOSITORY ANALYSIS SYSTEM")
    print("=" * 70)

    # -------------------------------------------------------------
    # Validate command-line input
    # -------------------------------------------------------------

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python3 main.py <github_repository>")

        print("\nExamples:")
        print("  python3 main.py octocat/Hello-World")

        print(
            "  python3 main.py "
            "https://github.com/octocat/Hello-World"
        )

        sys.exit(1)

    repository = sys.argv[1]

    print("\nRepository requested:")
    print(f"  {repository}")

    # -------------------------------------------------------------
    # STEP 1 - Fetch repository
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 1 - FETCHING GITHUB REPOSITORY")
    print("=" * 70)

    try:
        fetcher = RepositoryFetcher()

        repository_data = fetcher.fetch(repository)

        print("\nRepository fetched successfully.")

        print(
            f"Name: "
            f"{repository_data.get('name')}"
        )

        print(
            f"Full Name: "
            f"{repository_data.get('full_name')}"
        )

        print(
            f"Stars: "
            f"{repository_data.get('stars')}"
        )

        print(
            f"Forks: "
            f"{repository_data.get('forks')}"
        )

        print(
            f"Files: "
            f"{len(repository_data.get('files', []))}"
        )

        print(
            f"Source Files: "
            f"{len(repository_data.get('source_files', []))}"
        )

        print(
            f"Issues: "
            f"{len(repository_data.get('issues', []))}"
        )

        print(
            f"Pull Requests: "
            f"{len(repository_data.get('pull_requests', []))}"
        )

    except Exception as exc:
        print("\nERROR while fetching repository:")
        print(exc)
        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 2 - Build AI context
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 2 - BUILDING AI CONTEXT")
    print("=" * 70)

    try:
        context_builder = ContextBuilder()

        repository_context = context_builder.build(
            repository_data
        )

        print("\nAI context created successfully.")

        print(
            f"Context size: "
            f"{len(repository_context)} characters"
        )

    except Exception as exc:
        print("\nERROR while building context:")
        print(exc)
        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 3 - Initialize agents
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 3 - INITIALIZING AI AGENTS")
    print("=" * 70)

    try:
        repomind_crew = RepoMindCrew(
            repository_context=repository_context
        )

        print("\nRepoMind Crew initialized.")

        print("\nAgents:")

        print("  1. Repository Agent")
        print("  2. Architecture Agent")
        print("  3. Code Quality Agent")
        print("  4. Documentation Agent")
        print("  5. Security Agent")
        print("  6. Risk Agent")
        print("  7. Recommendation Agent")
        print("  8. Summary Agent")

    except Exception as exc:
        print("\nERROR while initializing Crew:")
        print(exc)
        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 4 - Run AI analysis
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 4 - RUNNING AI ANALYSIS")
    print("=" * 70)

    try:
        result = repomind_crew.run()

    except KeyboardInterrupt:
        print("\n\nAnalysis stopped by user.")
        sys.exit(0)

    except Exception as exc:
        print("\nERROR during AI analysis:")
        print(exc)
        sys.exit(1)

    # -------------------------------------------------------------
    # Preserve raw AI output
    # -------------------------------------------------------------

    raw_ai_report = str(result)

    print("\nAI analysis completed.")

    # -------------------------------------------------------------
    # STEP 5 - Validate raw AI analysis
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 5 - VALIDATING AI REPORT GROUNDING")
    print("=" * 70)

    try:
        ai_validation = validate_report(
            report_text=raw_ai_report,
            repository_context=repository_context,
        )

        print(
            f"\nAI grounding status: "
            f"{ai_validation.get('status')}"
        )

        print(
            f"AI evidence statements: "
            f"{ai_validation.get('evidence_count')}"
        )

        if ai_validation.get("warnings"):
            print("\nAI grounding warnings:")

            for warning in ai_validation.get(
                "warnings",
                [],
            ):
                print(f"  - {warning}")

    except Exception as exc:
        print("\nERROR during AI grounding validation:")
        print(exc)

        ai_validation = {
            "status": "WARNING",
            "warnings": [
                f"Grounding validation failed: {exc}"
            ],
            "unsupported_terms": [],
            "repository_files": [],
            "evidence_count": 0,
            "evidence_with_file_paths": [],
            "unsupported_evidence_count": 0,
        }

    # -------------------------------------------------------------
    # Deterministic finalization
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 6 - BUILDING GROUNDED FINAL REPORT")
    print("=" * 70)

    final_report_text = build_grounded_report(
        repository_data
    )

    print(
        "\nDeterministic grounded report created."
    )

    # -------------------------------------------------------------
    # STEP 7 - Validate final report
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 7 - VALIDATING FINAL REPORT")
    print("=" * 70)

    try:
        validation = validate_report(
            report_text=final_report_text,
            repository_context=repository_context,
        )

        print(
            f"\nFinal grounding status: "
            f"{validation.get('status')}"
        )

        print(
            f"Evidence statements: "
            f"{validation.get('evidence_count')}"
        )

        print(
            f"Collected repository files: "
            f"{len(validation.get('repository_files', []))}"
        )

        unsupported_terms = validation.get(
            "unsupported_terms",
            [],
        )

        if unsupported_terms:
            print("\nUnsupported terms detected:")

            for term in unsupported_terms:
                print(f"  - {term}")

        warnings = validation.get(
            "warnings",
            [],
        )

        if warnings:
            print("\nFinal grounding warnings:")

            for warning in warnings:
                print(f"  - {warning}")

        grounding_notice = build_grounding_notice(
            validation
        )

    except Exception as exc:
        print("\nERROR during final grounding validation:")
        print(exc)

        validation = {
            "status": "WARNING",
            "warnings": [
                f"Grounding validation failed: {exc}"
            ],
            "unsupported_terms": [],
            "repository_files": [],
            "evidence_count": 0,
            "evidence_with_file_paths": [],
            "unsupported_evidence_count": 0,
        }

        grounding_notice = build_grounding_notice(
            validation
        )

    # -------------------------------------------------------------
    # STEP 8 - Generate reports
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STEP 8 - GENERATING REPORTS")
    print("=" * 70)

    repository_name = repository_data.get(
        "full_name",
        repository_data.get(
            "name",
            "repository",
        ),
    )

    validated_report = (
        grounding_notice
        + "\n\n"
        + final_report_text
    )

    try:
        markdown_file = generate_markdown(
            result=validated_report,
            repository_name=repository_name,
        )

        json_file = generate_json(
            result=validated_report,
            repository_name=repository_name,
        )

        html_file = generate_html(
            result=validated_report,
            repository_name=repository_name,
        )

        print("\nReports generated successfully.")

        print(
            f"  Markdown: {markdown_file}"
        )

        print(
            f"  JSON:     {json_file}"
        )

        print(
            f"  HTML:     {html_file}"
        )

    except Exception as exc:
        print("\nERROR while generating reports:")
        print(exc)
        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 9 - Final output
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL REPOSITORY ANALYSIS")
    print("=" * 70)

    print(validated_report)

    print("\n" + "=" * 70)

    if validation.get("status") == "PASS":
        print(
            "RepoMind-AI analysis completed successfully."
        )
    else:
        print(
            "RepoMind-AI analysis completed with "
            "grounding warnings."
        )

    print("=" * 70)


if __name__ == "__main__":
    main()

