"""
RepoMind-AI
Complete multi-agent workflow test.
"""

from workflow.crew import RepoMindCrew


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

GROUNDING RULES
===============

Use only information present in this context.

Do not invent:

- programming languages
- filenames
- directories
- dependencies
- technologies
- architecture components
- security vulnerabilities
- source-code problems
- dates
- development practices

If information is missing, explicitly state:

"Not available in the provided context."
"""


def main():

    print("=" * 70)
    print("RepoMind-AI - COMPLETE MULTI-AGENT WORKFLOW")
    print("=" * 70)

    print("\nInitializing RepoMind Crew...")

    repomind_crew = RepoMindCrew(
        repository_context=REPOSITORY_CONTEXT
    )

    print("Crew initialized successfully.")

    print("\nStarting multi-agent analysis...")
    print("=" * 70)

    result = repomind_crew.run()

    print("\n")
    print("=" * 70)
    print("FINAL REPOSITORY ANALYSIS")
    print("=" * 70)

    print(result)

    print("=" * 70)
    print("RepoMind-AI analysis completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()