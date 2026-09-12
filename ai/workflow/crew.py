"""
RepoMind-AI
Main multi-agent CrewAI workflow.

The workflow runs repository analysis agents sequentially
and passes the appropriate previous findings to each stage.
"""

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
        #
        # IMPORTANT:
        # The summary receives the analysis findings but NOT the
        # raw repository-analysis task. This prevents the small
        # local model from falling back to raw GitHub JSON.
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
        # Execute workflow
        # ---------------------------------------------------------

        result = crew.kickoff()

        return result

