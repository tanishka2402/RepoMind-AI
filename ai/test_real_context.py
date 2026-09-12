"""
RepoMind-AI
Real GitHub Repository Context Test

This test:
1. Fetches a real GitHub repository
2. Builds repository context
3. Sends that context to the Hugging Face model
4. Prints the generated analysis

This test does NOT run the complete CrewAI workflow yet.
"""

import json

from github_service.github_client import GitHubClient
from llm.inference import InferenceEngine


REPOSITORY = "octocat/Hello-World"


def main():

    print("=" * 70)
    print("RepoMind-AI - REAL REPOSITORY CONTEXT TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1: Connect to GitHub
    # ---------------------------------------------------------

    print("\n[1/4] Connecting to GitHub...")

    client = GitHubClient()

    print("GitHub client initialized.")

    # ---------------------------------------------------------
    # STEP 2: Fetch repository
    # ---------------------------------------------------------

    print("\n[2/4] Fetching repository...")

    owner, repository = REPOSITORY.split("/", 1)
    repository_data = client.get_repository(owner, repository)

    print("Repository fetched successfully.")

    print("\nRepository:")
    print(
        json.dumps(
            repository_data,
            indent=2,
            default=str,
        )
    )

    # ---------------------------------------------------------
    # STEP 3: Build AI context
    # ---------------------------------------------------------

    print("\n[3/4] Building repository context...")

    context = json.dumps(
        repository_data,
        indent=2,
        default=str,
    )

    print("\nRepository context created.")

    print("-" * 70)
    print(context)
    print("-" * 70)

    # ---------------------------------------------------------
    # STEP 4: Send context to Hugging Face model
    # ---------------------------------------------------------

    print("\n[4/4] Sending context to Hugging Face model...")

    engine = InferenceEngine()

    prompt = f"""
You are RepoMind-AI, an expert GitHub repository analyzer.

Analyze the following repository context.

REPOSITORY CONTEXT
==================
{context}

Provide a concise technical analysis covering:

1. Repository purpose
2. Technology or language information
3. Repository structure
4. Development activity indicators
5. Potential strengths
6. Potential risks
7. Three actionable recommendations

Important:
- Use only information available in the repository context.
- Do not invent files, technologies, vulnerabilities, or features.
- Clearly distinguish observations from assumptions.
"""

    response = engine.generate(
        prompt=prompt,
        max_new_tokens=500,
        temperature=0.2,
        top_p=0.9,
    )

    print("\n")
    print("=" * 70)
    print("AI REPOSITORY ANALYSIS")
    print("=" * 70)
    print(response)
    print("=" * 70)

    print("\nReal repository context test completed successfully.")


if __name__ == "__main__":
    main()