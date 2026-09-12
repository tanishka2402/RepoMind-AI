from llm.crewai_adapter import HuggingFaceCrewLLM


def main():

    print("=" * 60)
    print("RepoMind-AI Hugging Face Adapter Test")
    print("=" * 60)

    llm = HuggingFaceCrewLLM()

    response = llm.call(
        """
You are RepoMind-AI.

Explain in three short points what a GitHub
repository analyzer does.
""",
        max_new_tokens=150,
        temperature=0.2,
    )

    print("\nMODEL RESPONSE")
    print("=" * 60)
    print(response)


if __name__ == "__main__":
    main()