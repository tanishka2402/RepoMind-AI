import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class BranchFetcher:
    """Fetch repository branches."""

    def __init__(self, client: GitHubClient | None = None):
        self.client = client or GitHubClient()

    def fetch(self, owner: str, repo: str, limit: int = 100):
        """Fetch branches and basic protection information."""

        repository = self.client.get_repository(owner, repo)
        branches = []

        for branch in repository.get_branches():
            protected = getattr(
                branch,
                "protected",
                False,
            )

            branches.append(
                {
                    "name": branch.name,
                    "protected": protected,
                    "commit_sha": (
                        branch.commit.sha
                        if branch.commit
                        else None
                    ),
                }
            )

            if len(branches) >= limit:
                break

        logger.info(
            "Fetched %d branches",
            len(branches),
        )

        return branches