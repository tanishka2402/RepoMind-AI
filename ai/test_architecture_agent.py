"""
RepoMind-AI
Architecture Agent integration test.
"""

from crewai import Crew, Process

from agents import create_architecture_agent
from workflow.tasks import create_architecture_task


REPOSITORY_CONTEXT = """
REPOSITORY FACTS
================

Repository:
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
[]

Languages:
Not available in the provided context.

Repository URL:
https://github.com/octocat/Hello-World
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - Architecture Agent Test")
    print("=" * 70)

    print("\nCreating Architecture Agent...")

    agent = create_architecture_agent()

    print("Architecture Agent created.")
    print("Agent role:", agent.role)

    print("\nCreating Architecture Task...")

    task = create_architecture_task(
        agent,
        REPOSITORY_CONTEXT,
    )

    print("Architecture Task created.")

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\nStarting Architecture Agent...")
    print("=" * 70)

    result = crew.kickoff()

    print("\n")
    print("=" * 70)
    print("ARCHITECTURE AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Architecture Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
