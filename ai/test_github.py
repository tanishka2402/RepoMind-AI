from github_service.github_client import GitHubClient


def main():
    print("Testing GitHub connection...")

    client = GitHubClient()

    repository = client.get_repository(
        "octocat",
        "Hello-World",
    )

    print("\nGitHub connection successful!")
    print("Repository:", repository.full_name)
    print("Stars:", repository.stargazers_count)
    print("Default branch:", repository.default_branch)


if __name__ == "__main__":
    main()
