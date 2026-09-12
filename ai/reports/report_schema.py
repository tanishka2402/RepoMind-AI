"""
RepoMind-AI Structured Report Schema.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Finding:
    """A single AI-generated repository finding."""

    category: str
    title: str
    description: str
    evidence: str
    severity: str = "info"
    recommendation: str = ""


@dataclass
class RepositoryReport:
    """Structured final repository analysis."""

    repository: str
    executive_summary: str = ""

    architecture: List[Finding] = field(default_factory=list)
    code_quality: List[Finding] = field(default_factory=list)
    documentation: List[Finding] = field(default_factory=list)
    security: List[Finding] = field(default_factory=list)
    risks: List[Finding] = field(default_factory=list)
    recommendations: List[Finding] = field(default_factory=list)

    def all_findings(self) -> List[Finding]:
        """Return every finding in the report."""

        return (
            self.architecture
            + self.code_quality
            + self.documentation
            + self.security
            + self.risks
            + self.recommendations
        )
