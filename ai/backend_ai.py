"""
Backend interface for RepoMind-AI.

This module provides a simple Python function that the
FastAPI backend can use to run repository analysis.
"""

from typing import Any, Dict

from github_service.repository_fetcher import (
    RepositoryFetcher,
)

from context.context_builder import (
    ContextBuilder,
)

from context.repository_intelligence import (
    build_repository_intelligence,
)

from workflow.crew import (
    RepoMindCrew,
)

from reports.report_validator import (
    validate_report,
)

from reports.scoring import (
    calculate_overall_from_report,
    score_repository_analysis,
)

from main import (
    build_grounded_report,
)

from reports.structured_analysis import (
    build_structured_analysis,
)


def analyze_repository(
    repository: str,
) -> Dict[str, Any]:
    """
    Run the complete RepoMind-AI repository-analysis pipeline.

    Pipeline:

        GitHub repository
            ↓
        RepositoryFetcher
            ↓
        Repository Intelligence
            ↓
        Repository context
            ↓
        CrewAI agents
            ↓
        Raw AI report
            ↓
        AI validation
            ↓
        Deterministic grounded report
            ↓
        Final validation
            ↓
        Structured analysis
            ↓
        Deterministic scoring
            ↓
        Backend response
    """

    # ============================================================
    # 1. Fetch repository
    # ============================================================

    fetcher = RepositoryFetcher()

    repository_data = fetcher.fetch(
        repository
    )

    # ============================================================
    # 2. Build deterministic repository intelligence
    # ============================================================

    repository_intelligence = (
        build_repository_intelligence(
            repository_data
        )
    )

    # ============================================================
    # 3. Build AI context
    # ============================================================

    context_builder = ContextBuilder()

    repository_context = context_builder.build(
        repository_data
    )

    # ============================================================
    # 4. Run CrewAI
    # ============================================================

    crew = RepoMindCrew(
        repository_context=repository_context
    )

    ai_result = crew.run()

    raw_ai_report = str(
        ai_result
    )

    # ============================================================
    # 5. Validate raw AI report
    # ============================================================

    ai_validation = validate_report(
        report_text=raw_ai_report,
        repository_context=repository_context,
    )

    # ============================================================
    # 6. Build deterministic grounded final report
    # ============================================================

    final_report = build_grounded_report(
        repository_data,
        repository_intelligence,
    )

    # ============================================================
    # 7. Validate final report
    # ============================================================

    final_validation = validate_report(
        report_text=final_report,
        repository_context=repository_context,
    )

    # ============================================================
    # 8. Build structured analysis
    # ============================================================

    structured_analysis = build_structured_analysis(
        repository_data=repository_data,
        raw_ai_report=raw_ai_report,
    )

    # ============================================================
    # 9. Add Repository Intelligence
    # ============================================================

    structured_analysis_data = (
        structured_analysis.to_dict()
    )

    structured_analysis_data[
        "repository_overview"
    ] = repository_intelligence

    # ============================================================
    # 10. Score structured analysis
    # ============================================================

    structured_analysis = score_repository_analysis(
        report=structured_analysis,
        repository_data=repository_data,
    )

    structured_analysis_data = (
        structured_analysis.to_dict()
    )

    # ============================================================
    # 11. Preserve Repository Intelligence after scoring
    # ============================================================

    structured_analysis_data[
        "repository_overview"
    ] = repository_intelligence

    # ============================================================
    # 12. Calculate overall score
    # ============================================================

    structured_analysis_data[
        "overall"
    ] = calculate_overall_from_report(
        structured_analysis
    )

    # ============================================================
    # 13. Return backend response
    # ============================================================

    return {
        "status": "completed",

        "repository": {
            "name": repository_data.get(
                "name"
            ),
            "full_name": repository_data.get(
                "full_name"
            ),
            "url": repository_data.get(
                "url"
            ),
            "default_branch": repository_data.get(
                "default_branch"
            ),
        },

        "analysis": {
            "report": final_report,

            "grounding_status": (
                final_validation.get(
                    "status"
                )
            ),

            "evidence_count": (
                final_validation.get(
                    "evidence_count",
                    0,
                )
            ),

            "warnings": (
                final_validation.get(
                    "warnings",
                    [],
                )
            ),

            "structured": (
                structured_analysis_data
            ),
        },

        "ai": {
            "grounding_status": (
                ai_validation.get(
                    "status"
                )
            ),

            "evidence_count": (
                ai_validation.get(
                    "evidence_count",
                    0,
                )
            ),
        },
    }