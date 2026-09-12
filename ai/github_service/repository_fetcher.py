"""
RepoMind-AI Repository Fetcher

Collects structured information from a GitHub repository
for downstream AI analysis.
"""

from typing import Any, Dict, List
from urllib.parse import urlparse

from .github_client import GitHubClient


class RepositoryURLParser:
    """Parse GitHub repository URLs or owner/name strings."""

    @staticmethod
    def parse(repository: str) -> tuple[str, str]:
        """Return (owner, repo_name) from a GitHub URL or short form."""
        return RepositoryFetcher._parse_repository(repository)


class RepositoryFetcher:
    """Fetch structured repository information from GitHub."""

    MAX_FILES = 100
    MAX_FILE_SIZE = 100_000

    SOURCE_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".kts",
        ".cs",
        ".scala",
        ".sh",
        ".bash",
        ".sql",
        ".html",
        ".css",
        ".scss",
        ".vue",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".md",
    }

    IGNORE_DIRECTORIES = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }

    def __init__(self, client: GitHubClient | None = None) -> None:
        self.client = client or GitHubClient()

    @staticmethod
    def _parse_repository(repository: str) -> tuple[str, str]:
        """Parse owner and repository name from a URL or owner/name string."""
        repository = repository.strip()

        if not repository:
            raise ValueError("Repository cannot be empty.")

        if repository.startswith(("http://", "https://")):
            parsed = urlparse(repository)
            if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
                raise ValueError("URL must point to GitHub.")
            parts = [part for part in parsed.path.strip("/").split("/") if part]
            if len(parts) < 2:
                raise ValueError("GitHub URL must contain owner and repository.")
            owner = parts[0]
            repo_name = parts[1]
        else:
            parts = repository.strip("/").split("/")
            if len(parts) != 2:
                raise ValueError("Repository must be in owner/name format.")
            owner = parts[0]
            repo_name = parts[1]

        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        return owner, repo_name

    def fetch(self, repository: str) -> Dict[str, Any]:
        """Fetch complete structured repository information."""
        owner, repo_name = self._parse_repository(repository)
        repo = self.client.get_repository(owner, repo_name)

        return {
            "name": getattr(repo, "name", None),
            "full_name": getattr(repo, "full_name", None),
            "owner": getattr(getattr(repo, "owner", None), "login", None),
            "description": getattr(repo, "description", None),
            "default_branch": getattr(repo, "default_branch", None),
            "stars": getattr(repo, "stargazers_count", 0),
            "forks": getattr(repo, "forks_count", 0),
            "watchers": getattr(repo, "watchers_count", 0),
            "open_issues": getattr(repo, "open_issues_count", 0),
            "url": getattr(repo, "html_url", None),
            "topics": self._get_topics(repo),
            "languages": self._get_languages(repo),
            "files": self._get_files(repo),
            "source_files": self._get_source_files(repo),
            "issues": self._get_issues(repo),
            "pull_requests": self._get_pull_requests(repo),
            "branches": self._get_branches(repo),
        }

    @staticmethod
    def _get_topics(repo: Any) -> List[str]:
        try:
            return list(repo.get_topics() or [])
        except Exception:
            return []

    @staticmethod
    def _get_languages(repo: Any) -> Dict[str, int]:
        try:
            return dict(repo.get_languages() or {})
        except Exception:
            return {}

    def _get_files(self, repo: Any) -> List[str]:
        try:
            contents = repo.get_contents("")
            return [item.path for item in contents if getattr(item, "path", None)]
        except Exception:
            return []

    def _get_source_files(self, repo: Any) -> List[Dict[str, str]]:
        source_files: List[Dict[str, str]] = []
        try:
            self._collect_directory(repo=repo, path="", source_files=source_files)
        except Exception:
            return []
        return source_files[: self.MAX_FILES]

    def _collect_directory(
        self,
        repo: Any,
        path: str,
        source_files: List[Dict[str, str]],
    ) -> None:
        if len(source_files) >= self.MAX_FILES:
            return

        try:
            contents = repo.get_contents(path)
        except Exception:
            return

        for item in contents:
            if len(source_files) >= self.MAX_FILES:
                return
            item_path = getattr(item, "path", "")
            if not item_path or self._should_ignore(item_path):
                continue

            if getattr(item, "type", None) == "dir":
                self._collect_directory(repo=repo, path=item_path, source_files=source_files)
            elif getattr(item, "type", None) == "file":
                if not self._is_source_file(item.name):
                    continue
                if getattr(item, "size", 0) and item.size > self.MAX_FILE_SIZE:
                    continue
                file_data = self._read_file(item)
                if file_data is not None:
                    source_files.append(file_data)

    @staticmethod
    def _read_file(file_item: Any) -> Dict[str, str] | None:
        try:
            content = file_item.decoded_content.decode("utf-8", errors="replace")
            return {"path": file_item.path, "content": content}
        except Exception:
            return None

    def _is_source_file(self, filename: str) -> bool:
        filename_lower = filename.lower()
        return any(filename_lower.endswith(extension) for extension in self.SOURCE_EXTENSIONS)

    def _should_ignore(self, path: str) -> bool:
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        return any(part in self.IGNORE_DIRECTORIES for part in parts)

    @staticmethod
    def _get_issues(repo: Any) -> List[Dict[str, Any]]:
        try:
            issues = repo.get_issues(state="all")
            results = []
            for issue in issues[:100]:
                if getattr(issue, "pull_request", None):
                    continue
                results.append(
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "url": issue.html_url,
                    }
                )
            return results
        except Exception:
            return []

    @staticmethod
    def _get_pull_requests(repo: Any) -> List[Dict[str, Any]]:
        try:
            pulls = repo.get_pulls(state="all")
            return [
                {
                    "number": pull.number,
                    "title": pull.title,
                    "state": pull.state,
                    "url": pull.html_url,
                }
                for pull in pulls[:100]
            ]
        except Exception:
            return []

    @staticmethod
    def _get_branches(repo: Any) -> List[str]:
        try:
            return [branch.name for branch in repo.get_branches() if getattr(branch, "name", None)]
        except Exception:
            return []
