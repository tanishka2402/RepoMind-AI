"""
RepoMind-AI
GitHub -> RepositoryFetcher -> ContextBuilder integration test.
"""

from github_service.repository_fetcher import RepositoryFetcher
from context.context_builder import ContextBuilder


def main():

    repository = "octocat/Hello-World"

    print("=" * 70)
    print("RepoMind-AI GitHub -> Context Pipeline")
    print("=" * 70)

    print("\n1. Creating RepositoryFetcher...")

    fetcher = RepositoryFetcher()

    print("RepositoryFetcher created.")

    print("\n2. Fetching repository...")
    print(f"Repository: {repository}")

    repository_data = fetcher.fetch(repository)

    print("Repository fetched successfully.")

    print("\n3. Creating ContextBuilder...")

    builder = ContextBuilder()

    print("ContextBuilder created.")

    print("\n4. Building AI context...")

    context = builder.build(repository_data)

    print("AI context created successfully.")

    print("\n")
    print("=" * 70)
    print("GENERATED AI CONTEXT")
    print("=" * 70)

    print(context)

    print("=" * 70)
    print("Pipeline test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
