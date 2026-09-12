import logging

from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class PullRequestFetcher:
    """Fetch pull requests from a repository."""

    def __init__(self, client: GitHubClient | None = None):
        self.client = client or GitHubClient()

    def fetch(self, owner: str, repo: str, limit: int = 100):
        """Fetch open and closed pull requests."""

        repository = self.client.get_repository(owner, repo)
        pull_requests = []

        for pr in repository.get_pulls(state="all"):
            pull_requests.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body or "",
                    "state": pr.state,
                    "author": (
                        pr.user.login
                        if pr.user
                        else None
                    ),
                    "source_branch": (
                        pr.head.ref
                        if pr.head
                        else None
                    ),
                    "target_branch": (
                        pr.base.ref
                        if pr.base
                        else None
                    ),
                    "merged": pr.merged,
                    "draft": pr.draft,
                    "created_at": (
                        pr.created_at.isoformat()
                        if pr.created_at
                        else None
                    ),
                    "updated_at": (
                        pr.updated_at.isoformat()
                        if pr.updated_at
                        else None
                    ),
                    "url": pr.html_url,
                }
            )

            if len(pull_requests) >= limit:
                break

        logger.info(
            "Fetched %d pull requests",
            len(pull_requests),
        )

        return pull_requests