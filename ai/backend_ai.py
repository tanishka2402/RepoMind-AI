"""
Backend interface for RepoMind-AI.

This module provides a simple Python function that the
FastAPI backend can use to run repository analysis.
"""
from security.scanner import scan_repository

from typing import Any, Dict
from contextlib import contextmanager
import logging
from time import perf_counter

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


logger = logging.getLogger(__name__)


@contextmanager
def _timed_stage(stage: str, **fields: Any):
    """Log elapsed wall-clock time for a pipeline stage, including failures."""
    started = perf_counter()
    try:
        yield
    except Exception:
        logger.exception(
            "RepoMind timing | stage=%s | status=error | elapsed_seconds=%.3f | details=%s",
            stage,
            perf_counter() - started,
            fields,
        )
        raise
    else:
        logger.info(
            "RepoMind timing | stage=%s | status=ok | elapsed_seconds=%.3f | details=%s",
            stage,
            perf_counter() - started,
            fields,
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

    with _timed_stage("analysis_pipeline_total", repository=repository):
        # ============================================================
        # 1. Fetch repository
        # ============================================================

        with _timed_stage("github_fetch", repository=repository):
            fetcher = RepositoryFetcher()
            repository_data = fetcher.fetch(repository)

        # Static security scan: never execute repository files.
        with _timed_stage("security_scan"):
            security_scan = scan_repository(repository_data)


        # ============================================================
        # 2. Build deterministic repository intelligence
        # ============================================================

        with _timed_stage("repository_intelligence"):
            repository_intelligence = build_repository_intelligence(
                repository_data
            )

        # ============================================================
        # 3. Build AI context
        # ============================================================

        with _timed_stage("context_build"):
            context_builder = ContextBuilder()
            repository_context = context_builder.build(repository_data)

        # ============================================================
        # 4. Run CrewAI
        # ============================================================

        with _timed_stage("crewai_run"):
            crew = RepoMindCrew(repository_context=repository_context)
            ai_result = crew.run()
            raw_ai_report = str(ai_result)

        # ============================================================
        # 5. Validate raw AI report
        # ============================================================

        with _timed_stage("raw_ai_report_validation"):
            ai_validation = validate_report(
                report_text=raw_ai_report,
                repository_context=repository_context,
            )

        # ============================================================
        # 6. Build deterministic grounded final report
        # ============================================================

        with _timed_stage("grounded_report_build"):
            final_report = build_grounded_report(
                repository_data,
                repository_intelligence,
            )

        # ============================================================
        # 7. Validate final report
        # ============================================================

        with _timed_stage("final_report_validation"):
            final_validation = validate_report(
                report_text=final_report,
                repository_context=repository_context,
            )

        # ============================================================
        # 8. Build structured analysis
        # ============================================================

        with _timed_stage("structured_analysis_build"):
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

        with _timed_stage("repository_scoring"):
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

        with _timed_stage("overall_score_calculation"):
            structured_analysis_data[
                "overall"
            ] = calculate_overall_from_report(structured_analysis)

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
                "security_scan": security_scan,

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