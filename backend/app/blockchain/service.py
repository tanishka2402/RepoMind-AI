"""
High-level blockchain service for RepoMind-AI.
"""

from typing import Any, Dict

from .client import BlockchainClient
from .hasher import (
    report_hash,
    repository_hash,
)


class BlockchainService:
    """Register and verify RepoMind analysis records."""

    def __init__(
        self,
        client: BlockchainClient | None = None,
    ):
        self.client = (
            client
            if client is not None
            else BlockchainClient()
        )

    def register_analysis(
        self,
        analysis_id: int,
        repository: str,
        summary_report: str,
    ) -> Dict[str, Any]:
        """Hash and register a summary report."""

        repo_digest = repository_hash(
            repository
        )

        report_digest = report_hash(
            summary_report
        )

        blockchain_result = (
            self.client.register_analysis(
                analysis_id=analysis_id,
                repository_hash=repo_digest,
                report_hash=report_digest,
                summary_report=summary_report,
            )
        )

        return {
            "analysis_id": analysis_id,
            "repository_hash": repo_digest,
            "report_hash": report_digest,
            "summary_report": summary_report,
            **blockchain_result,
        }

    def verify_analysis(
        self,
        analysis_id: int,
        summary_report: str,
    ) -> bool:
        """Verify the supplied report against blockchain."""

        digest = report_hash(
            summary_report
        )

        return self.client.verify_report(
            analysis_id=analysis_id,
            report_hash=digest,
        )
