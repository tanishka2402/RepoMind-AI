"""
RepoMind-AI
Repository Agent integration test.

Flow:

GitHub Repository
        ↓
Repository Context
        ↓
Repository Agent
        ↓
CrewAI
        ↓
Hugging Face LLM
        ↓
Repository Analysis
"""

from crewai import Crew, Process

from agents import create_repository_agent
from workflow.tasks import create_repository_task


REPOSITORY_CONTEXT = """
Repository Name:
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

Branches:
3

Files:
1

Issues Collected:
100

Pull Requests Collected:
100

Topics:
None

Repository URL:
https://github.com/octocat/Hello-World
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - Repository Agent Test")
    print("=" * 70)

    # ---------------------------------------------------------
    # Create Repository Agent
    # ---------------------------------------------------------

    print("\nCreating Repository Agent...")

    repository_agent = create_repository_agent()

    print("Repository Agent created.")

    print("\nAgent role:")
    print(repository_agent.role)

    # ---------------------------------------------------------
    # Create Repository Task
    # ---------------------------------------------------------

    print("\nCreating Repository Task...")

    repository_task = create_repository_task(
        repository_agent,
        REPOSITORY_CONTEXT,
    )

    print("Repository Task created.")

    # ---------------------------------------------------------
    # Create Crew
    # ---------------------------------------------------------

    print("\nCreating test Crew...")

    crew = Crew(
        agents=[
            repository_agent,
        ],
        tasks=[
            repository_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    print("Crew created successfully.")

    # ---------------------------------------------------------
    # Run agent
    # ---------------------------------------------------------

    print("\nStarting Repository Agent...")
    print("=" * 70)

    result = crew.kickoff()

    # ---------------------------------------------------------
    # Display result
    # ---------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("REPOSITORY AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Repository Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
    