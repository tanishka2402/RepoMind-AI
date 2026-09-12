"""
RepoMind-AI
Summary Agent integration test.
"""

from crewai import Crew, Process

from agents import create_summary_agent
from workflow.tasks import create_summary_task


ANALYSIS_CONTEXT = """
REPOSMIND-AI ANALYSIS CONTEXT
==============================

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


IMPORTANT GROUNDING RULES
=========================

Create a concise final repository summary using ONLY
the information provided above.

Do not invent:

- programming languages
- filenames
- directories
- dependencies
- technologies
- architecture
- security vulnerabilities
- source-code characteristics
- dates
- development practices

If information is unavailable, explicitly state:

"Not available in the provided context."

Clearly distinguish facts from interpretations.

The final summary should contain:

1. Repository Overview
2. Repository Statistics
3. Available Technical Information
4. Development Indicators
5. Limitations of the Analysis
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - Summary Agent Test")
    print("=" * 70)

    print("\nCreating Summary Agent...")

    agent = create_summary_agent()

    print("Summary Agent created.")
    print("Agent role:", agent.role)

    print("\nCreating Summary Task...")

    task = create_summary_task(
        agent,
        ANALYSIS_CONTEXT,
    )

    print("Summary Task created.")

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\nStarting Summary Agent...")
    print("=" * 70)

    result = crew.kickoff()

    print("\n")
    print("=" * 70)
    print("SUMMARY AGENT RESULT")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("Summary Agent test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
