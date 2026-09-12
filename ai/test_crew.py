"""
Test the complete RepoMind-AI CrewAI workflow
using a real repository context.

This test intentionally uses a small repository first
to avoid excessive model inference on the MacBook.
"""

from workflow.crew import RepoMindCrew


REPOSITORY_CONTEXT = """
GitHub Repository:

Name:
Hello-World

Full Name:
octocat/Hello-World

Description:
My first repository on GitHub!

Default Branch:
master

Stars:
3770

Forks:
6503

Watchers:
3770

Open Issues:
6911

Repository URL:
https://github.com/octocat/Hello-World

Languages:
GitHub API returned language information.

Topics:
No repository topics were reported.

Files:
1

Issues collected:
100

Pull Requests collected:
100

Branches:
3
"""


def main():

    print("=" * 70)
    print("RepoMind-AI CrewAI Integration Test")
    print("=" * 70)

    print("\nCreating RepoMind Crew...")

    crew = RepoMindCrew(
        repository_context=REPOSITORY_CONTEXT
    )

    print("Crew created successfully.")

    print("\nStarting multi-agent analysis...")
    print("=" * 70)

    result = crew.run()

    print("\n")
    print("=" * 70)
    print("FINAL REPOSITORY ANALYSIS")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("CrewAI test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
    