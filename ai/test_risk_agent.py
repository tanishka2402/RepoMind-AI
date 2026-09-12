"""
RepoMind-AI
Risk Agent integration test.
"""

from crewai import Crew, Process

from agents import create_risk_agent
from workflow.tasks import create_risk_task


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

Pull Requests:
100

Topics:
[]

Languages:
Not available in the provided context.

Repository URL:
https://github.com/octocat/Hello-World

IMPORTANT:
Only identify risks supported by the supplied repository facts.

Do not invent:
- source-code problems
- security vulnerabilities
- dependencies
- technologies
- architecture components
- missing files
- development practices

If evidence is insufficient, explicitly state:
"Insufficient information to assess this risk."

Separate:
1. Observed facts
2. Potential risks
3. Evidence
4. Confidence
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - Risk Agent Test")
    print("=" * 70)

    print("\nCreating Risk Agent...")

    agent = create_risk_agent()

    print("Risk Agent created.")
    print("Agent role:", agent.role)

    print("\nCreating Risk Task...")

    task = create_risk_task(
        agent,
        REPOSITORY_CONTEXT,
    )

    print("Risk Task created.")

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\nStarting Risk Agent...")
    print("=" * 70)

    result = crew.kickoff()

    print("\n")
    print("=" * 70)
    print("RISK AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Risk Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
