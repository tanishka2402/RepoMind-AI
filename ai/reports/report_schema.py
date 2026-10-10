"""
Structured report schema for RepoMind-AI.

This module defines the normalized data structures used by the
AI analysis pipeline, deterministic grounding layer, scoring engine,
and backend API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


VALID_SEVERITIES = {
    "info",
    "low",
    "medium",
    "high",
    "critical",
}


@dataclass
class Finding:
    """
    A single evidence-backed repository finding.
    """

    category: str
    title: str
    description: str
    evidence: str
    severity: str = "info"
    recommendation: str = ""

    def normalized(self) -> "Finding":
        """
        Return a cleaned and normalized copy of the finding.
        """

        severity = self.severity.lower().strip()

        if severity not in VALID_SEVERITIES:
            severity = "info"

        return Finding(
            category=self.category.strip(),
            title=self.title.strip(),
            description=self.description.strip(),
            evidence=self.evidence.strip(),
            severity=severity,
            recommendation=self.recommendation.strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the finding to a JSON-serializable dictionary.
        """

        item = self.normalized()

        return {
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "evidence": item.evidence,
            "severity": item.severity,
            "recommendation": item.recommendation,
        }


@dataclass
class CategoryAnalysis:
    """
    Structured analysis for one repository-analysis category.

    score:
        Deterministic repository-health score from 0 to 100.

    severity:
        Risk classification derived from the deterministic score.

    confidence:
        Evidence coverage from 0 to 100.
    """

    score: Optional[int] = None
    severity: str = "info"
    confidence: int = 0

    findings: List[Finding] = field(default_factory=list)

    evidence: List[str] = field(default_factory=list)

    recommendations: List[str] = field(default_factory=list)

    def normalized(self) -> "CategoryAnalysis":
        """
        Return a cleaned and normalized copy of the category.
        """

        severity = self.severity.lower().strip()

        if severity not in VALID_SEVERITIES:
            severity = "info"

        normalized_score: Optional[int]

        if self.score is None:
            normalized_score = None
        else:
            normalized_score = max(
                0,
                min(100, int(self.score)),
            )

        normalized_confidence = max(
            0,
            min(100, int(self.confidence)),
        )

        return CategoryAnalysis(
            score=normalized_score,
            severity=severity,
            confidence=normalized_confidence,
            findings=[
                finding.normalized()
                for finding in self.findings
            ],
            evidence=[
                item.strip()
                for item in self.evidence
                if item and item.strip()
            ],
            recommendations=[
                item.strip()
                for item in self.recommendations
                if item and item.strip()
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the category to a JSON-serializable dictionary.
        """

        item = self.normalized()

        return {
            "score": item.score,
            "severity": item.severity,
            "confidence": item.confidence,
            "findings": [
                finding.to_dict()
                for finding in item.findings
            ],
            "evidence": item.evidence,
            "recommendations": item.recommendations,
        }


@dataclass
class RepositoryReport:
    """
    Complete structured repository analysis.
    """

    repository: str

    executive_summary: str = ""

    architecture: CategoryAnalysis = field(
        default_factory=CategoryAnalysis
    )

    code_quality: CategoryAnalysis = field(
        default_factory=CategoryAnalysis
    )

    documentation: CategoryAnalysis = field(
        default_factory=CategoryAnalysis
    )

    security: CategoryAnalysis = field(
        default_factory=CategoryAnalysis
    )

    risk: CategoryAnalysis = field(
        default_factory=CategoryAnalysis
    )

    recommendations: CategoryAnalysis = field(
        default_factory=CategoryAnalysis
    )

    def all_findings(self) -> List[Finding]:
        """
        Return all findings across analysis categories.
        """

        return (
            self.architecture.findings
            + self.code_quality.findings
            + self.documentation.findings
            + self.security.findings
            + self.risk.findings
            + self.recommendations.findings
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the repository report into a JSON-serializable dictionary.
        """

        return {
            "repository": self.repository,
            "executive_summary": self.executive_summary.strip(),

            "architecture": (
                self.architecture.to_dict()
            ),

            "code_quality": (
                self.code_quality.to_dict()
            ),

            "documentation": (
                self.documentation.to_dict()
            ),

            "security": (
                self.security.to_dict()
            ),

            "risk": (
                self.risk.to_dict()
            ),

            "recommendations": (
                self.recommendations.to_dict()
            ),
        }