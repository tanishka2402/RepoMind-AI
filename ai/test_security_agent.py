"""
RepoMind-AI
Security Agent integration test.
"""

from crewai import Crew, Process

from agents import create_security_agent
from workflow.tasks import create_security_task


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
Only analyze information explicitly present in this context.
Do not invent source-code vulnerabilities.
Do not claim that a file, dependency, secret, API,
authentication mechanism, or security configuration exists
unless it is explicitly present in the context.
If security information is unavailable, say so.
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - Security Agent Test")
    print("=" * 70)

    print("\nCreating Security Agent...")

    agent = create_security_agent()

    print("Security Agent created.")
    print("Agent role:", agent.role)

    print("\nCreating Security Task...")

    task = create_security_task(
        agent,
        REPOSITORY_CONTEXT,
    )

    print("Security Task created.")

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\nStarting Security Agent...")
    print("=" * 70)

    result = crew.kickoff()

    print("\n")
    print("=" * 70)
    print("SECURITY AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Security Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
