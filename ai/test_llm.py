from llm.inference import InferenceEngine


def main():

    print("=" * 60)
    print("RepoMind-AI Hugging Face LLM Test")
    print("=" * 60)

    engine = InferenceEngine()

    prompt = """
You are analyzing a GitHub repository.

Repository:
RepoMind-AI

Technologies:
Python, FastAPI, Next.js, PostgreSQL,
Hugging Face Transformers and CrewAI.

Give a short explanation of what this project
is designed to do.
"""

    print("\nGenerating response...\n")

    response = engine.generate(
        prompt,
        max_new_tokens=150,
        temperature=0.2,
    )

    print("=" * 60)
    print("MODEL RESPONSE")
    print("=" * 60)
    print(response)


if __name__ == "__main__":
    main()
