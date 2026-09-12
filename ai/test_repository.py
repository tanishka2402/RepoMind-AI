import json

from github_service.github_client import GitHubClient
from github_service.repository_fetcher import RepositoryFetcher


def main():

    print("Starting repository analysis...")

    client = GitHubClient()

    fetcher = RepositoryFetcher(client)

    repository_url = (
        "https://github.com/octocat/Hello-World"
    )

    data = fetcher.fetch(repository_url)

    print("\n========== REPOSITORY ==========")

    print(
        json.dumps(
            {
                key: data[key]
                for key in (
                    "name",
                    "full_name",
                    "owner",
                    "description",
                    "default_branch",
                    "stars",
                    "forks",
                    "watchers",
                    "open_issues",
                    "url",
                )
            },
            indent=2,
        )
    )

    print(
        "\nLanguages:",
        data["languages"],
    )

    print(
        "\nTopics:",
        data["topics"],
    )

    print(
        "\nFiles:",
        len(data["files"]),
    )

    print(
        "Issues:",
        len(data["issues"]),
    )

    print(
        "Pull Requests:",
        len(data["pull_requests"]),
    )

    print(
        "Branches:",
        len(data["branches"]),
    )

    with open(
        "github_analysis.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nSaved analysis to "
        "github_analysis.json"
    )

    print(
        "\nRepository collection successful!"
    )


if __name__ == "__main__":
    main()