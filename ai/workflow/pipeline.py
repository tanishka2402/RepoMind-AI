"""
RepoMind-AI end-to-end AI analysis pipeline.
"""

from .crew import RepoMindCrew


class AnalysisPipeline:
    """
    Executes repository analysis using CrewAI.
    """

    def __init__(self, repository_context: str):
        self.repository_context = repository_context

    def run(self):
        """
        Run the complete agentic analysis.
        """

        if not self.repository_context.strip():
            raise ValueError(
                "Repository context cannot be empty."
            )

        crew = RepoMindCrew(
            self.repository_context
        )

        return crew.run()