"""
RepoMind-AI
Recommendation Agent integration test.
"""

from crewai import Crew, Process

from agents import create_recommendation_agent
from workflow.tasks import create_recommendation_task


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


ANALYSIS RULES
==============

Only make recommendations supported by the information above.

Do not invent:
- source-code problems
- programming languages
- dependencies
- architecture components
- security vulnerabilities
- files
- technologies
- development practices

Recommendations must clearly distinguish:
1. Evidence
2. Recommendation
3. Reason
4. Priority

If evidence is insufficient, say:
"Insufficient information for a specific recommendation."
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - Recommendation Agent Test")
    print("=" * 70)

    print("\nCreating Recommendation Agent...")

    agent = create_recommendation_agent()

    print("Recommendation Agent created.")
    print("Agent role:", agent.role)

    print("\nCreating Recommendation Task...")

    task = create_recommendation_task(
        agent,
        REPOSITORY_CONTEXT,
    )

    print("Recommendation Task created.")

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\nStarting Recommendation Agent...")
    print("=" * 70)

    result = crew.kickoff()

    print("\n")
    print("=" * 70)
    print("RECOMMENDATION AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Recommendation Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
