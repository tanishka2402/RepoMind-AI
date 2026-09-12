"""
Backend interface for RepoMind-AI.

This module provides a simple Python function that the
FastAPI backend can use to run repository analysis.
"""

from typing import Any, Dict

from github_service.repository_fetcher import RepositoryFetcher
from context.context_builder import ContextBuilder
from workflow.crew import RepoMindCrew

from reports.report_validator import validate_report
from main import build_grounded_report


def analyze_repository(repository: str) -> Dict[str, Any]:
    """
    Run the RepoMind-AI analysis pipeline for a repository.

    Parameters
    ----------
    repository:
        GitHub repository in owner/name format or GitHub URL.

    Returns
    -------
    Dict[str, Any]
        Structured analysis result.
    """

    # ---------------------------------------------------------
    # 1. Fetch repository
    # ---------------------------------------------------------

    fetcher = RepositoryFetcher()

    repository_data = fetcher.fetch(repository)

    # ---------------------------------------------------------
    # 2. Build AI context
    # ---------------------------------------------------------

    context_builder = ContextBuilder()

    repository_context = context_builder.build(
        repository_data
    )

    # ---------------------------------------------------------
    # 3. Run AI agents
    # ---------------------------------------------------------

    crew = RepoMindCrew(
        repository_context=repository_context
    )

    ai_result = crew.run()

    raw_ai_report = str(ai_result)

    # ---------------------------------------------------------
    # 4. Validate raw AI result
    # ---------------------------------------------------------

    ai_validation = validate_report(
        report_text=raw_ai_report,
        repository_context=repository_context,
    )

    # ---------------------------------------------------------
    # 5. Build grounded final report
    # ---------------------------------------------------------

    final_report = build_grounded_report(
        repository_data
    )

    # ---------------------------------------------------------
    # 6. Validate final report
    # ---------------------------------------------------------

    final_validation = validate_report(
        report_text=final_report,
        repository_context=repository_context,
    )

    # ---------------------------------------------------------
    # 7. Return structured result
    # ---------------------------------------------------------

    return {
        "status": "completed",

        "repository": {
            "name": repository_data.get("name"),
            "full_name": repository_data.get("full_name"),
            "url": repository_data.get("url"),
            "default_branch": repository_data.get(
                "default_branch"
            ),
        },

        "analysis": {
            "report": final_report,
            "grounding_status": final_validation.get(
                "status"
            ),
            "evidence_count": final_validation.get(
                "evidence_count",
                0,
            ),
            "warnings": final_validation.get(
                "warnings",
                [],
            ),
        },

        "ai": {
            "grounding_status": ai_validation.get(
                "status"
            ),
            "evidence_count": ai_validation.get(
                "evidence_count",
                0,
            ),
        },
    }

