
"""
Fast single-pass CrewAI workflow for RepoMind-AI.

Performance improvements:
- Runs one comprehensive analysis task instead of eight sequential tasks.
- Reuses the existing summary agent and master-analysis task.
- Keeps evidence-first analysis and all eight report sections.
- Logs elapsed time for agent initialization and model execution.

Repository fetching, static security scanning, validation,
grounded report generation, scoring, and persistence remain
in their existing backend layers.
"""

import logging
import time

from crewai import Crew, Process

from agents import create_summary_agent
from workflow.tasks import create_master_analysis_task


logger = logging.getLogger(__name__)


class RepoMindCrew:
    """Run a focused, single-pass repository analysis."""

    def __init__(self, repository_context: str):
        self.repository_context = repository_context

    def run(self):
        total_start = time.perf_counter()

        logger.info("RepoMind-AI: Starting single-pass analysis")

        # --------------------------------------------------------
        # 1. Initialize one agent
        # --------------------------------------------------------

        stage_start = time.perf_counter()

        agent = create_summary_agent()

        logger.info(
            "RepoMind timing | stage=agent_initialization | "
            "elapsed_seconds=%.3f",
            time.perf_counter() - stage_start,
        )

        # --------------------------------------------------------
        # 2. Build one comprehensive task
        # --------------------------------------------------------

        task = create_master_analysis_task(
            agent=agent,
            repository_context=self.repository_context,
        )

        # --------------------------------------------------------
        # 3. Execute one LLM analysis task
        # --------------------------------------------------------

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )

        logger.info("RepoMind-AI: Running master analysis")

        llm_start = time.perf_counter()

        try:
            result = crew.kickoff()

        except Exception:
            logger.exception(
                "RepoMind-AI master analysis failed after %.2f seconds",
                time.perf_counter() - llm_start,
            )
            raise

        llm_elapsed = time.perf_counter() - llm_start
        total_elapsed = time.perf_counter() - total_start

        logger.info(
            "RepoMind timing | stage=master_analysis | "
            "elapsed_seconds=%.3f",
            llm_elapsed,
        )

        logger.info(
            "RepoMind timing | stage=crew_total | "
            "elapsed_seconds=%.3f",
            total_elapsed,
        )

        return result
