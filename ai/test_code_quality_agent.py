"""
RepoMind-AI
Code Quality Agent integration test.
"""

from crewai import Crew, Process

from agents import create_code_quality_agent
from workflow.tasks import create_code_quality_task


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
    print("RepoMind-AI - Code Quality Agent Test")
    print("=" * 70)

    print("\nCreating Code Quality Agent...")

    agent = create_code_quality_agent()

    print("Code Quality Agent created.")
    print("Agent role:", agent.role)

    print("\nCreating Code Quality Task...")

    task = create_code_quality_task(
        agent,
        REPOSITORY_CONTEXT,
    )

    print("Code Quality Task created.")

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\nStarting Code Quality Agent...")
    print("=" * 70)

    result = crew.kickoff()

    print("\n")
    print("=" * 70)
    print("CODE QUALITY AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Code Quality Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
