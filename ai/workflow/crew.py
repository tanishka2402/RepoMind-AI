
"""
RepoMind-AI
Main multi-agent CrewAI workflow.

The workflow runs repository analysis agents sequentially
and passes the appropriate previous findings to each stage.
"""

import time

from crewai import Crew, Process

from agents import (
    create_repository_agent,
    create_architecture_agent,
    create_code_quality_agent,
    create_documentation_agent,
    create_security_agent,
    create_risk_agent,
    create_recommendation_agent,
    create_summary_agent,
)

from workflow.tasks import (
    create_repository_task,
    create_architecture_task,
    create_code_quality_task,
    create_documentation_task,
    create_security_task,
    create_risk_task,
    create_recommendation_task,
    create_summary_task,
)


class RepoMindCrew:
    """Main orchestrator for RepoMind-AI agents."""

    def __init__(self, repository_context: str):
        self.repository_context = repository_context

    def run(self):
        """Create and execute the RepoMind-AI workflow."""

        total_start = time.perf_counter()

        print("\n" + "=" * 60)
        print("RepoMind-AI: Initializing multi-agent analysis")
        print("=" * 60)

        # ---------------------------------------------------------
        # Create agents
        # ---------------------------------------------------------

        repository_agent = create_repository_agent()
        architecture_agent = create_architecture_agent()
        code_quality_agent = create_code_quality_agent()
        documentation_agent = create_documentation_agent()
        security_agent = create_security_agent()
        risk_agent = create_risk_agent()
        recommendation_agent = create_recommendation_agent()
        summary_agent = create_summary_agent()

        # ---------------------------------------------------------
        # Repository analysis
        # ---------------------------------------------------------

        repository_task = create_repository_task(
            repository_agent,
            self.repository_context,
        )

        # ---------------------------------------------------------
        # Architecture analysis
        # ---------------------------------------------------------

        architecture_task = create_architecture_task(
            architecture_agent,
            self.repository_context,
            context_tasks=[
                repository_task,
            ],
        )

        # ---------------------------------------------------------
        # Code quality analysis
        # ---------------------------------------------------------

        code_quality_task = create_code_quality_task(
            code_quality_agent,
            self.repository_context,
            context_tasks=[
                repository_task,
            ],
        )

        # ---------------------------------------------------------
        # Documentation analysis
        # ---------------------------------------------------------

        documentation_task = create_documentation_task(
            documentation_agent,
            self.repository_context,
            context_tasks=[
                repository_task,
            ],
        )

        # ---------------------------------------------------------
        # Security analysis
        # ---------------------------------------------------------

        security_task = create_security_task(
            security_agent,
            self.repository_context,
            context_tasks=[
                repository_task,
            ],
        )

        # ---------------------------------------------------------
        # Risk analysis
        # ---------------------------------------------------------

        risk_task = create_risk_task(
            risk_agent,
            self.repository_context,
            context_tasks=[
                repository_task,
                architecture_task,
                code_quality_task,
                documentation_task,
                security_task,
            ],
        )

        # ---------------------------------------------------------
        # Recommendations
        # ---------------------------------------------------------

        recommendation_task = create_recommendation_task(
            recommendation_agent,
            self.repository_context,
            context_tasks=[
                architecture_task,
                code_quality_task,
                documentation_task,
                security_task,
                risk_task,
            ],
        )

        # ---------------------------------------------------------
        # Final summary
        # ---------------------------------------------------------

        summary_task = create_summary_task(
            summary_agent,
            self.repository_context,
            context_tasks=[
                architecture_task,
                code_quality_task,
                documentation_task,
                security_task,
                risk_task,
                recommendation_task,
            ],
        )

        # ---------------------------------------------------------
        # Create Crew
        # ---------------------------------------------------------

        crew = Crew(
            agents=[
                repository_agent,
                architecture_agent,
                code_quality_agent,
                documentation_agent,
                security_agent,
                risk_agent,
                recommendation_agent,
                summary_agent,
            ],
            tasks=[
                repository_task,
                architecture_task,
                code_quality_task,
                documentation_task,
                security_task,
                risk_task,
                recommendation_task,
                summary_task,
            ],
            process=Process.sequential,
            verbose=True,
        )

        # ---------------------------------------------------------
        # Execute workflow and measure duration
        # ---------------------------------------------------------

        print("\nStarting CrewAI analysis...")
        analysis_start = time.perf_counter()

        try:
            result = crew.kickoff()
        except Exception as exc:
            elapsed = time.perf_counter() - analysis_start

            print("\n" + "=" * 60)
            print("RepoMind-AI analysis failed")
            print(f"Elapsed time before failure: {elapsed:.2f} seconds")
            print(f"Error: {exc}")
            print("=" * 60)

            raise

        analysis_elapsed = time.perf_counter() - analysis_start
        total_elapsed = time.perf_counter() - total_start

        print("\n" + "=" * 60)
        print("RepoMind-AI analysis timing")
        print(f"CrewAI execution: {analysis_elapsed:.2f} seconds")
        print(f"Total workflow time: {total_elapsed:.2f} seconds")
        print("=" * 60)

        return result
