"""
RepoMind-AI
Main entry point.

Pipeline:

GitHub URL
    ↓
RepositoryFetcher
    ↓
Repository Intelligence
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
from context.repository_intelligence import (
    build_repository_intelligence,
)
from workflow.crew import RepoMindCrew

from reports.report_validator import (
    validate_report,
    build_grounding_notice,
)

from reports.markdown_generator import generate_markdown
from reports.json_generator import generate_json
from reports.html_generator import generate_html


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------


IGNORED_LANGUAGE_METADATA = {
    "url",
    "links",
    "metadata",
}


DOCUMENTATION_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".txt",
}


NON_SOURCE_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".lock",
}


def get_file_path(item: Any) -> str:
    """
    Safely extract a repository file path.
    """

    if isinstance(item, str):
        return item

    if isinstance(item, dict):
        return str(
            item.get("path")
            or item.get("name")
            or ""
        )

    return ""


def is_documentation_file(path: str) -> bool:
    """
    Return True when a repository path represents documentation.
    """

    path_lower = path.lower()

    return any(
        path_lower.endswith(extension)
        for extension in DOCUMENTATION_EXTENSIONS
    )


def is_non_source_file(path: str) -> bool:
    """
    Return True for documentation/configuration/metadata files
    that should not be presented as source-code files.
    """

    path_lower = path.lower()

    if is_documentation_file(path_lower):
        return True

    return any(
        path_lower.endswith(extension)
        for extension in NON_SOURCE_EXTENSIONS
    )


def get_clean_source_files(
    repository_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Return source files suitable for the final report.

    README.md, TODO.md and other documentation/configuration files
    are intentionally excluded from source-code reporting.

    This does not modify repository_data.
    """

    raw_source_files = repository_data.get(
        "source_files",
        [],
    )

    cleaned: List[Dict[str, Any]] = []

    for item in raw_source_files:

        path = get_file_path(item)

        if not path:
            continue

        if is_non_source_file(path):
            continue

        if isinstance(item, dict):
            cleaned.append(item)
        else:
            cleaned.append(
                {
                    "path": path,
                }
            )

    return cleaned


def get_documentation_files(
    repository_data: Dict[str, Any],
) -> List[str]:
    """
    Identify documentation files from the complete repository file list.

    Documentation is intentionally derived from `files`, not
    `source_files`, because README.md and TODO.md are not source code.
    """

    files = repository_data.get(
        "files",
        [],
    )

    documentation_files: List[str] = []

    for item in files:

        path = get_file_path(item)

        if not path:
            continue

        if is_documentation_file(path):
            documentation_files.append(path)

    return documentation_files


def get_clean_language_metadata(
    languages: Any,
) -> Dict[str, int]:
    """
    Clean GitHub language metadata.

    GitHub's PyGithub response may contain a `url` metadata key.
    That is an API URL, not a programming language.
    """

    if not isinstance(languages, dict):
        return {}

    cleaned: Dict[str, int] = {}

    for language, evidence in languages.items():

        language_name = str(language).strip()

        if not language_name:
            continue

        if language_name.lower() in IGNORED_LANGUAGE_METADATA:
            continue

        try:
            cleaned[language_name] = int(evidence)
        except (TypeError, ValueError):
            continue

    return cleaned


def get_intelligence_languages(
    repository_intelligence: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Return cleaned programming-language information from
    Repository Intelligence.

    Actual Repository Intelligence schema:

        {
            "language": "Python",
            "evidence": 1234,
            "percentage": 72.5
        }
    """

    languages = repository_intelligence.get(
        "languages",
        [],
    )

    cleaned: List[Dict[str, Any]] = []

    if not isinstance(languages, list):
        return cleaned

    for item in languages:

        if not isinstance(item, dict):
            continue

        language = str(
            item.get("language", "")
        ).strip()

        if not language:
            continue

        if language.lower() in IGNORED_LANGUAGE_METADATA:
            continue

        cleaned.append(
            {
                "language": language,
                "evidence": item.get(
                    "evidence",
                    0,
                ),
                "percentage": item.get(
                    "percentage",
                    0,
                ),
            }
        )

    return cleaned


# -----------------------------------------------------------------
# Repository Intelligence section
# -----------------------------------------------------------------


def build_repository_intelligence_section(
    repository_intelligence: Dict[str, Any],
) -> str:
    """
    Convert deterministic Repository Intelligence into a readable
    report section.

    This section appears before Architecture, Code Quality,
    Documentation, Security, Risk and Recommendations.
    """

    report_parts: List[str] = []

    intelligence = repository_intelligence or {}

    # -------------------------------------------------------------
    # Actual Repository Intelligence schema
    #
    # repository
    # project_type
    # domain
    # purpose
    # executive_summary
    # languages
    # technology_stack
    # repository_structure
    # major_components
    # codebase_composition
    # workflow
    # important_modules
    # repository_statistics
    # target_users
    # analysis_scope
    # -------------------------------------------------------------

    repository = intelligence.get(
        "repository",
        {},
    )

    if not isinstance(repository, dict):
        repository = {}

    project_type = intelligence.get(
        "project_type",
        "Unknown",
    )

    domain = intelligence.get(
        "domain",
        "General software project",
    )

    purpose = intelligence.get(
        "purpose",
        "Purpose could not be determined from the collected evidence.",
    )

    executive_summary = intelligence.get(
        "executive_summary",
        "Repository intelligence could not be generated.",
    )

    languages = get_intelligence_languages(
        intelligence
    )

    technology_stack = intelligence.get(
        "technology_stack",
        {},
    )

    major_components = intelligence.get(
        "major_components",
        [],
    )

    codebase_composition = intelligence.get(
        "codebase_composition",
        [],
    )

    workflow = intelligence.get(
        "workflow",
        [],
    )

    important_modules = intelligence.get(
        "important_modules",
        [],
    )

    repository_statistics = intelligence.get(
        "repository_statistics",
        {},
    )

    target_users = intelligence.get(
        "target_users",
        [],
    )

    # -------------------------------------------------------------
    # Section title
    # -------------------------------------------------------------

    report_parts.append(
        "REPOSITORY INTELLIGENCE"
    )

    # -------------------------------------------------------------
    # Executive summary
    # -------------------------------------------------------------

    report_parts.append(
        "EXECUTIVE SUMMARY"
    )

    report_parts.append(
        str(executive_summary)
    )

    # -------------------------------------------------------------
    # Repository identity
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "REPOSITORY IDENTITY"
    )

    report_parts.append(
        f"Project Type: {project_type}"
    )

    report_parts.append(
        f"Domain: {domain}"
    )

    report_parts.append(
        f"Purpose: {purpose}"
    )

    if repository:

        repository_name = repository.get(
            "name"
        )

        full_name = repository.get(
            "full_name"
        )

        default_branch = repository.get(
            "default_branch"
        )

        if repository_name:
            report_parts.append(
                f"Repository Name: {repository_name}"
            )

        if full_name:
            report_parts.append(
                f"Full Name: {full_name}"
            )

        if default_branch:
            report_parts.append(
                f"Default Branch: {default_branch}"
            )

    # -------------------------------------------------------------
    # Programming languages
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "PROGRAMMING LANGUAGES"
    )

    if languages:

        for language in languages:

            name = language.get(
                "language",
                "Unknown",
            )

            percentage = language.get(
                "percentage",
                0,
            )

            evidence = language.get(
                "evidence",
                0,
            )

            try:
                percentage_text = (
                    f"{float(percentage):.1f}%"
                )
            except (
                TypeError,
                ValueError,
            ):
                percentage_text = str(
                    percentage
                )

            report_parts.append(
                f"- {name}: "
                f"{percentage_text} "
                f"({evidence} bytes)"
            )

    else:

        report_parts.append(
            "- No programming-language information was detected."
        )

    # -------------------------------------------------------------
    # Technology stack
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "TECHNOLOGY STACK"
    )

    if isinstance(
        technology_stack,
        dict,
    ):

        found_stack = False

        for category, technologies in technology_stack.items():

            if not technologies:
                continue

            found_stack = True

            readable_category = (
                str(category)
                .replace("_", " ")
                .title()
            )

            if isinstance(
                technologies,
                list,
            ):

                values = ", ".join(
                    str(item)
                    for item in technologies
                )

            else:

                values = str(
                    technologies
                )

            report_parts.append(
                f"- {readable_category}: {values}"
            )

        if not found_stack:

            report_parts.append(
                "- No additional technology-stack indicators were detected."
            )

    else:

        report_parts.append(
            f"- {technology_stack}"
        )

    # -------------------------------------------------------------
    # Major components
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "MAJOR COMPONENTS"
    )

    if isinstance(
        major_components,
        list,
    ) and major_components:

        for component in major_components:

            if isinstance(
                component,
                dict,
            ):

                name = component.get(
                    "name",
                    "Unknown",
                )

                purpose_text = component.get(
                    "purpose",
                    "",
                )

                evidence = component.get(
                    "evidence",
                    "",
                )

                if purpose_text:

                    report_parts.append(
                        f"- {name}: {purpose_text}"
                    )

                else:

                    report_parts.append(
                        f"- {name}"
                    )

                if evidence:

                    report_parts.append(
                        f"  Evidence: {evidence}"
                    )

            else:

                report_parts.append(
                    f"- {component}"
                )

    else:

        report_parts.append(
            "- No major components were identified."
        )

    # -------------------------------------------------------------
    # Codebase composition
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "CODEBASE COMPOSITION"
    )

    if isinstance(
        codebase_composition,
        list,
    ) and codebase_composition:

        for item in codebase_composition:

            report_parts.append(
                f"- {item}"
            )

    elif isinstance(
        codebase_composition,
        dict,
    ) and codebase_composition:

        for key, value in codebase_composition.items():

            readable_key = (
                str(key)
                .replace("_", " ")
                .title()
            )

            report_parts.append(
                f"- {readable_key}: {value}"
            )

    else:

        report_parts.append(
            "- Codebase composition information is unavailable."
        )

    # -------------------------------------------------------------
    # How the repository works
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "HOW THE REPOSITORY WORKS"
    )

    if isinstance(
        workflow,
        list,
    ) and workflow:

        for index, step in enumerate(
            workflow,
            start=1,
        ):

            if isinstance(
                step,
                dict,
            ):

                description = step.get(
                    "description",
                    step.get(
                        "step",
                        str(step),
                    ),
                )

            else:

                description = str(step)

            report_parts.append(
                f"{index}. {description}"
            )

    else:

        report_parts.append(
            "- Repository workflow could not be inferred."
        )

    # -------------------------------------------------------------
    # Important modules/files
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "IMPORTANT MODULES AND FILES"
    )

    if isinstance(
        important_modules,
        list,
    ) and important_modules:

        for item in important_modules:

            if isinstance(
                item,
                dict,
            ):

                name = item.get(
                    "name",
                    item.get(
                        "path",
                        "Unknown",
                    ),
                )

                purpose_text = item.get(
                    "purpose",
                    item.get(
                        "reason",
                        "",
                    ),
                )

                if purpose_text:

                    report_parts.append(
                        f"- {name}: {purpose_text}"
                    )

                else:

                    report_parts.append(
                        f"- {name}"
                    )

            else:

                report_parts.append(
                    f"- {item}"
                )

    else:

        report_parts.append(
            "- No important modules or files were identified."
        )

    # -------------------------------------------------------------
    # Repository statistics
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "REPOSITORY STATISTICS"
    )

    if isinstance(
        repository_statistics,
        dict,
    ) and repository_statistics:

        for key, value in repository_statistics.items():

            readable_key = (
                str(key)
                .replace("_", " ")
                .title()
            )

            report_parts.append(
                f"- {readable_key}: {value}"
            )

    else:

        report_parts.append(
            "- Repository statistics are unavailable."
        )

    # -------------------------------------------------------------
    # Target users
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "TARGET USERS / USE CASE"
    )

    if isinstance(
        target_users,
        list,
    ) and target_users:

        for user in target_users:

            if isinstance(
                user,
                dict,
            ):

                name = user.get(
                    "name",
                    user.get(
                        "type",
                        "User",
                    ),
                )

                description = user.get(
                    "description",
                    "",
                )

                if description:

                    report_parts.append(
                        f"- {name}: {description}"
                    )

                else:

                    report_parts.append(
                        f"- {name}"
                    )

            else:

                report_parts.append(
                    f"- {user}"
                )

    elif target_users:

        report_parts.append(
            f"- {target_users}"
        )

    else:

        report_parts.append(
            "- Target users could not be determined from the collected evidence."
        )

    return "\n".join(
        report_parts
    )


# -----------------------------------------------------------------
# Deterministic grounded report builder
# -----------------------------------------------------------------


def build_grounded_report(
    repository_data: Dict[str, Any],
    repository_intelligence: Dict[str, Any],
) -> str:
    """
    Build a conservative final report directly from collected
    repository data and deterministic Repository Intelligence.

    The local LLM is still used for repository analysis, but
    malformed or unsupported model output must not become the
    final verified repository report.
    """

    name = (
        repository_data.get("name")
        or "Unknown"
    )

    full_name = (
        repository_data.get("full_name")
        or name
    )

    description = repository_data.get(
        "description"
    )

    default_branch = (
        repository_data.get(
            "default_branch"
        )
        or "Unavailable"
    )

    stars = repository_data.get(
        "stars",
        0,
    )

    forks = repository_data.get(
        "forks",
        0,
    )

    watchers = repository_data.get(
        "watchers",
        0,
    )

    open_issues = repository_data.get(
        "open_issues",
        0,
    )

    # -------------------------------------------------------------
    # Clean source files
    # -------------------------------------------------------------

    clean_source_files = get_clean_source_files(
        repository_data
    )

    documentation_files = get_documentation_files(
        repository_data
    )

    # -------------------------------------------------------------
    # Clean language metadata
    # -------------------------------------------------------------

    languages = get_clean_language_metadata(
        repository_data.get(
            "languages",
            {},
        )
    )

    # -------------------------------------------------------------
    # Repository collections
    # -------------------------------------------------------------

    files = repository_data.get(
        "files",
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

    report_parts.append(
        "EXECUTIVE SUMMARY"
    )

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
        f"The fetcher collected {len(files)} "
        f"repository files and "
        f"{len(clean_source_files)} source files "
        f"for direct source inspection."
    )

    report_parts.append(
        f"The repository also contains "
        f"{len(documentation_files)} documentation files."
    )

    report_parts.append(
        "The findings below are restricted to information "
        "observed by the repository collection pipeline."
    )

    # -------------------------------------------------------------
    # Repository Overview
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "REPOSITORY OVERVIEW"
    )

    report_parts.append(
        "CATEGORY: Repository"
    )

    report_parts.append(
        "TITLE: Repository metadata"
    )

    report_parts.append(
        "SEVERITY: info"
    )

    report_parts.append(
        f"DESCRIPTION: The analyzed repository is "
        f"{full_name}. "
        f"The default branch is "
        f"{default_branch}."
    )

    report_parts.append(
        f"EVIDENCE: Repository metadata reports "
        f"full_name={full_name} and "
        f"default_branch={default_branch}."
    )

    report_parts.append(
        "RECOMMENDATION: Continue reviewing the repository "
        "using the collected source files and GitHub metadata."
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

    # Prefer deterministic Repository Intelligence.
    intelligence_languages = get_intelligence_languages(
        repository_intelligence
    )

    if intelligence_languages:

        intelligence_language_names = ", ".join(
            item["language"]
            for item in intelligence_languages
        )

        report_parts.append(
            "DESCRIPTION: The Repository Intelligence layer "
            "identified the following programming languages: "
            f"{intelligence_language_names}."
        )

        report_parts.append(
            "EVIDENCE: Repository Intelligence calculated "
            "language evidence from the collected repository data."
        )

        report_parts.append(
            "RECOMMENDATION: Treat these languages as the "
            "cleaned programming-language information for this report."
        )

    elif languages:

        language_names = ", ".join(
            languages.keys()
        )

        report_parts.append(
            "DESCRIPTION: The GitHub language metadata "
            "identifies the following observed languages: "
            f"{language_names}."
        )

        report_parts.append(
            f"EVIDENCE: GitHub language metadata lists "
            f"{language_names}."
        )

        report_parts.append(
            "RECOMMENDATION: Treat the collected language "
            "metadata as the observed technology information "
            "for this report."
        )

    else:

        report_parts.append(
            "DESCRIPTION: No language metadata was returned "
            "by the repository collection pipeline."
        )

        report_parts.append(
            "EVIDENCE: The collected repository language "
            "metadata is empty."
        )

        report_parts.append(
            "RECOMMENDATION: Review the repository source "
            "files for language information."
        )

    # -------------------------------------------------------------
    # Repository Intelligence
    # -------------------------------------------------------------

    report_parts.append("")

    report_parts.append(
        build_repository_intelligence_section(
            repository_intelligence
        )
    )

    # -------------------------------------------------------------
    # Architecture
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "ARCHITECTURE FINDINGS"
    )

    if clean_source_files:

        source_paths = [
            get_file_path(item)
            for item in clean_source_files
            if get_file_path(item)
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
            "DESCRIPTION: No source files were collected "
            "for direct inspection."
        )

        report_parts.append(
            "EVIDENCE: The repository collection pipeline "
            "returned zero source files."
        )

        report_parts.append(
            "RECOMMENDATION: Review the repository contents "
            "directly if deeper source-level architecture "
            "analysis is required."
        )

    # -------------------------------------------------------------
    # Code Quality
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "CODE QUALITY FINDINGS"
    )

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
        f"DESCRIPTION: Code-quality observations are limited "
        f"to the {len(clean_source_files)} source files "
        f"collected for direct source inspection."
    )

    if clean_source_files:

        evidence_paths = [
            get_file_path(item)
            for item in clean_source_files
            if get_file_path(item)
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
    report_parts.append(
        "DOCUMENTATION FINDINGS"
    )

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
            "DESCRIPTION: Documentation files were collected "
            "from the repository."
        )

        report_parts.append(
            "EVIDENCE: Collected documentation files: "
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
            "TITLE: Documentation coverage"
        )

        report_parts.append(
            "SEVERITY: info"
        )

        report_parts.append(
            "DESCRIPTION: No documentation file was collected "
            "for inspection."
        )

        report_parts.append(
            "EVIDENCE: The collected repository file paths "
            "contain no recognized documentation file."
        )

        report_parts.append(
            "RECOMMENDATION: Review repository documentation "
            "separately if documentation is required."
        )

    # -------------------------------------------------------------
    # Security
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "SECURITY FINDINGS"
    )

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
        "limited to the repository information and source "
        "files collected by the pipeline."
    )

    if clean_source_files:

        security_paths = [
            get_file_path(item)
            for item in clean_source_files
            if get_file_path(item)
        ]

        report_parts.append(
            "EVIDENCE: Security review scope includes the "
            "collected source files: "
            + ", ".join(security_paths)
            + "."
        )

    else:

        report_parts.append(
            "EVIDENCE: No source files were collected "
            "for security inspection."
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
    report_parts.append(
        "RISK ASSESSMENT"
    )

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
        f"{len(files)} collected repository files and "
        f"{len(clean_source_files)} collected source files."
    )

    report_parts.append(
        f"EVIDENCE: Repository collection returned "
        f"{len(files)} repository files, "
        f"{len(clean_source_files)} source files, "
        f"{len(documentation_files)} documentation files, "
        f"{len(branches)} branches, "
        f"{len(issues)} issues, and "
        f"{len(pull_requests)} pull requests."
    )

    report_parts.append(
        "RECOMMENDATION: Treat findings outside the collected "
        "repository information as requiring additional verification."
    )

    # -------------------------------------------------------------
    # Recommendations
    # -------------------------------------------------------------

    report_parts.append("")
    report_parts.append(
        "RECOMMENDATIONS"
    )

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
        f"EVIDENCE: The repository analysis pipeline collected "
        f"{len(clean_source_files)} source files, "
        f"{len(files)} repository files, and "
        f"{len(documentation_files)} documentation files."
    )

    report_parts.append(
        "RECOMMENDATION: Continue using explicit repository "
        "evidence when producing analysis findings."
    )

    return "\n".join(
        report_parts
    )


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
        print(
            "  python3 main.py <github_repository>"
        )

        print("\nExamples:")

        print(
            "  python3 main.py octocat/Hello-World"
        )

        print(
            "  python3 main.py "
            "https://github.com/octocat/Hello-World"
        )

        sys.exit(1)

    repository = sys.argv[1]

    print("\nRepository requested:")
    print(
        f"  {repository}"
    )

    # -------------------------------------------------------------
    # STEP 1 - Fetch repository
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 1 - FETCHING GITHUB REPOSITORY"
    )
    print("=" * 70)

    try:

        fetcher = RepositoryFetcher()

        repository_data = fetcher.fetch(
            repository
        )

        print(
            "\nRepository fetched successfully."
        )

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
            f"Raw Source Files: "
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

        print(
            "\nERROR while fetching repository:"
        )

        print(exc)

        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 2 - Build Repository Intelligence
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 2 - BUILDING REPOSITORY INTELLIGENCE"
    )
    print("=" * 70)

    try:

        repository_intelligence = (
            build_repository_intelligence(
                repository_data
            )
        )

        print(
            "\nRepository Intelligence created successfully."
        )

        print(
            f"Project Type: "
            f"{repository_intelligence.get('project_type')}"
        )

        print(
            f"Domain: "
            f"{repository_intelligence.get('domain')}"
        )

        intelligence_languages = (
            get_intelligence_languages(
                repository_intelligence
            )
        )

        print(
            "Languages: "
            + ", ".join(
                item["language"]
                for item in intelligence_languages
            )
            if intelligence_languages
            else "Languages: None detected"
        )

        print(
            f"Major Components: "
            f"{len(repository_intelligence.get('major_components', []))}"
        )

    except Exception as exc:

        print(
            "\nERROR while building Repository Intelligence:"
        )

        print(exc)

        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 3 - Build AI context
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 3 - BUILDING AI CONTEXT"
    )
    print("=" * 70)

    try:

        context_builder = ContextBuilder()

        repository_context = (
            context_builder.build(
                repository_data
            )
        )

        print(
            "\nAI context created successfully."
        )

        print(
            f"Context size: "
            f"{len(repository_context)} characters"
        )

    except Exception as exc:

        print(
            "\nERROR while building context:"
        )

        print(exc)

        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 4 - Initialize agents
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 4 - INITIALIZING AI AGENTS"
    )
    print("=" * 70)

    try:

        repomind_crew = RepoMindCrew(
            repository_context=repository_context
        )

        print(
            "\nRepoMind Crew initialized."
        )

        print("\nAgents:")

        print(
            "  1. Repository Agent"
        )

        print(
            "  2. Architecture Agent"
        )

        print(
            "  3. Code Quality Agent"
        )

        print(
            "  4. Documentation Agent"
        )

        print(
            "  5. Security Agent"
        )

        print(
            "  6. Risk Agent"
        )

        print(
            "  7. Recommendation Agent"
        )

        print(
            "  8. Summary Agent"
        )

    except Exception as exc:

        print(
            "\nERROR while initializing Crew:"
        )

        print(exc)

        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 5 - Run AI analysis
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 5 - RUNNING AI ANALYSIS"
    )
    print("=" * 70)

    try:

        result = repomind_crew.run()

    except KeyboardInterrupt:

        print(
            "\n\nAnalysis stopped by user."
        )

        sys.exit(0)

    except Exception as exc:

        print(
            "\nERROR during AI analysis:"
        )

        print(exc)

        sys.exit(1)

    raw_ai_report = str(
        result
    )

    print(
        "\nAI analysis completed."
    )

    # -------------------------------------------------------------
    # STEP 6 - Validate raw AI analysis
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 6 - VALIDATING AI REPORT GROUNDING"
    )
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

        if ai_validation.get(
            "warnings"
        ):

            print(
                "\nAI grounding warnings:"
            )

            for warning in ai_validation.get(
                "warnings",
                [],
            ):

                print(
                    f"  - {warning}"
                )

    except Exception as exc:

        print(
            "\nERROR during AI grounding validation:"
        )

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
    # STEP 7 - Deterministic finalization
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 7 - BUILDING GROUNDED FINAL REPORT"
    )
    print("=" * 70)

    final_report_text = (
        build_grounded_report(
            repository_data,
            repository_intelligence,
        )
    )

    print(
        "\nDeterministic grounded report created."
    )

    # -------------------------------------------------------------
    # STEP 8 - Validate final report
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 8 - VALIDATING FINAL REPORT"
    )
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

        unsupported_terms = (
            validation.get(
                "unsupported_terms",
                [],
            )
        )

        if unsupported_terms:

            print(
                "\nUnsupported terms detected:"
            )

            for term in unsupported_terms:

                print(
                    f"  - {term}"
                )

        warnings = (
            validation.get(
                "warnings",
                [],
            )
        )

        if warnings:

            print(
                "\nFinal grounding warnings:"
            )

            for warning in warnings:

                print(
                    f"  - {warning}"
                )

        grounding_notice = (
            build_grounding_notice(
                validation
            )
        )

    except Exception as exc:

        print(
            "\nERROR during final grounding validation:"
        )

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

        grounding_notice = (
            build_grounding_notice(
                validation
            )
        )

    # -------------------------------------------------------------
    # STEP 9 - Generate reports
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "STEP 9 - GENERATING REPORTS"
    )
    print("=" * 70)

    repository_name = (
        repository_data.get(
            "full_name",
            repository_data.get(
                "name",
                "repository",
            ),
        )
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

        print(
            "\nReports generated successfully."
        )

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

        print(
            "\nERROR while generating reports:"
        )

        print(exc)

        sys.exit(1)

    # -------------------------------------------------------------
    # STEP 10 - Final output
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "FINAL REPOSITORY ANALYSIS"
    )
    print("=" * 70)

    print(
        validated_report
    )

    print(
        "\n" + "=" * 70
    )

    if validation.get(
        "status"
    ) == "PASS":

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