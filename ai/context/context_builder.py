
"""
RepoMind-AI Context Builder.

Builds a compact, grounded context for the AI agents.

The context intentionally avoids sending large raw GitHub
issue and pull-request datasets to the local language model.

The goal is to give the model:

1. Repository facts
2. A small summary of issues and pull requests
3. Actual collected files
4. Actual source code

while avoiding unnecessary API noise.
"""

import json
from typing import Any, Dict, List

from .preprocessor import SourcePreprocessor


class ContextBuilder:
    """Build compact grounded AI context."""

    MAX_ISSUES = 10
    MAX_PULL_REQUESTS = 10
    MAX_BRANCHES = 20
    MAX_FILES = 100

    def __init__(self) -> None:
        self.source_preprocessor = SourcePreprocessor()

    def build(self, repository_data: Dict[str, Any]) -> str:
        """
        Build grounded repository context.

        The context is intentionally compact so that the local
        language model can focus on source code and meaningful
        repository facts.
        """

        if not repository_data:
            raise ValueError(
                "Repository data cannot be empty."
            )

        source_context = self.source_preprocessor.process(
            repository_data.get(
                "source_files",
                [],
            )
        )

        repository_facts = self._build_repository_facts(
            repository_data
        )

        return (
            "REPOSITORY FACTS\n"
            "================\n\n"
            "The following information was collected directly "
            "from GitHub.\n\n"
            "GROUNDING RULES:\n"
            "- Treat only the information below as repository facts.\n"
            "- Do not invent files, frameworks, dependencies, "
            "features, architecture, or vulnerabilities.\n"
            "- Do not assume technologies that are not shown.\n"
            "- If information is unavailable, say so explicitly.\n"
            "- Source-code claims must reference an actual file path.\n"
            "- Distinguish observed facts from AI analysis.\n\n"
            f"{repository_facts}\n\n"
            f"{source_context}"
        )

    def _build_repository_facts(
        self,
        repository_data: Dict[str, Any],
    ) -> str:
        """
        Build a compact JSON representation of repository facts.
        """

        facts = {
            "repository": {
                "name": repository_data.get("name"),
                "full_name": repository_data.get("full_name"),
                "owner": repository_data.get("owner"),
                "description": repository_data.get("description"),
                "default_branch": repository_data.get(
                    "default_branch"
                ),
                "url": repository_data.get("url"),
            },

            "statistics": {
                "stars": repository_data.get("stars"),
                "forks": repository_data.get("forks"),
                "watchers": repository_data.get("watchers"),
                "open_issues": repository_data.get(
                    "open_issues"
                ),
            },

            "languages": self._compact_languages(
                repository_data.get(
                    "languages",
                    {},
                )
            ),

            "topics": self._limit_list(
                repository_data.get(
                    "topics",
                    [],
                ),
                20,
            ),

            "files": self._limit_list(
                repository_data.get(
                    "files",
                    [],
                ),
                self.MAX_FILES,
            ),

            "branches": self._limit_list(
                repository_data.get(
                    "branches",
                    [],
                ),
                self.MAX_BRANCHES,
            ),

            "issues": self._compact_issues(
                repository_data.get(
                    "issues",
                    [],
                )
            ),

            "pull_requests": self._compact_pull_requests(
                repository_data.get(
                    "pull_requests",
                    [],
                )
            ),
        }

        return json.dumps(
            facts,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    def _compact_issues(
        self,
        issues: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Keep only a small number of useful issue fields.
        """

        compacted = []

        for issue in issues[: self.MAX_ISSUES]:
            compacted.append(
                {
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "state": issue.get("state"),
                }
            )

        return compacted

    def _compact_pull_requests(
        self,
        pull_requests: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Keep only a small number of useful pull-request fields.
        """

        compacted = []

        for pull_request in pull_requests[
            : self.MAX_PULL_REQUESTS
        ]:
            compacted.append(
                {
                    "number": pull_request.get(
                        "number"
                    ),
                    "title": pull_request.get(
                        "title"
                    ),
                    "state": pull_request.get(
                        "state"
                    ),
                }
            )

        return compacted

    def _compact_languages(
        self,
        languages: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Return language information without unnecessary data.
        """

        if not isinstance(languages, dict):
            return {}

        return {
            str(name): value
            for name, value in languages.items()
        }

    def _limit_list(
        self,
        values: Any,
        maximum: int,
    ) -> List[Any]:
        """
        Safely limit a list to a maximum number of items.
        """

        if not isinstance(values, list):
            return []

        return values[:maximum]


