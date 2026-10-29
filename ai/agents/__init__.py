from crewai import Agent
from llm.crewai_adapter import HuggingFaceCrewLLM


_SHARED_LLM = None


def _get_shared_llm():
	global _SHARED_LLM
	if _SHARED_LLM is None:
		_SHARED_LLM = HuggingFaceCrewLLM()
	return _SHARED_LLM


def _create_agent(role: str, goal: str, backstory: str, llm=None) -> Agent:
	if llm is None:
		llm = _get_shared_llm()

	return Agent(
		role=role,
		goal=goal,
		backstory=backstory,
		llm=llm,
		verbose=True,
	)


def create_repository_agent(llm=None) -> Agent:
	return _create_agent(
		"Repository Analyst",
		"Understand and summarize the repository using only its provided context.",
		"You are a careful software engineer who identifies repository purpose, structure, technologies, and development indicators.",
		llm,
	)


def create_architecture_agent(llm=None) -> Agent:
	return _create_agent(
		"Software Architect",
		"Assess the repository architecture, organization, scalability, and maintainability.",
		"You are an experienced architect who evaluates technical structure and clearly separates evidence from recommendations.",
		llm,
	)


def create_code_quality_agent(llm=None) -> Agent:
	return _create_agent(
		"Code Quality Analyst",
		"Evaluate code quality, testing, dependencies, maintainability, and technical debt indicators.",
		"You are a pragmatic engineer focused on actionable quality improvements supported by repository evidence.",
		llm,
	)


def create_documentation_agent(llm=None) -> Agent:
	return _create_agent(
		"Documentation Analyst",
		"Assess documentation completeness, clarity, setup guidance, and usability.",
		"You specialize in developer documentation and identify gaps without inventing unavailable information.",
		llm,
	)


def create_security_agent(llm=None) -> Agent:
	return _create_agent(
		"Security Analyst",
		"Identify security observations and potential risks supported by the repository context.",
		"You are a security-minded engineer who distinguishes confirmed findings from possible risks.",
		llm,
	)


def create_risk_agent(llm=None) -> Agent:
	return _create_agent(
		"Technical Risk Analyst",
		"Identify, prioritize, and explain technical and project risks in the repository.",
		"You assess impact and evidence across architecture, dependencies, testing, security, and maintenance.",
		llm,
	)


def create_recommendation_agent(llm=None) -> Agent:
	return _create_agent(
		"Engineering Advisor",
		"Produce practical, prioritized recommendations based on the repository analysis.",
		"You turn supported observations into clear improvements that developers can act on.",
		llm,
	)


def create_summary_agent(llm=None) -> Agent:
	return _create_agent(
		"Analysis Summarizer",
		"Synthesize the workflow findings into an accurate and useful repository summary.",
		"You communicate technical findings concisely while preserving evidence, limitations, and priorities.",
		llm,
	)
def create_master_agent(llm=None) -> Agent:
    """Create the single orchestrator responsible for the complete report."""
    return _create_agent(
        "RepoMind Master Orchestrator",
        (
            "Analyze the supplied repository context in one focused pass and produce "
            "a concise, evidence-grounded report covering repository overview, "
            "architecture, code quality, documentation, security observations, risks, "
            "and prioritized recommendations."
        ),
        (
            "You are a senior software engineer coordinating repository analysis. "
            "Use only the provided context, cite actual file paths, distinguish facts "
            "from inference, acknowledge missing evidence, avoid duplicating findings, "
            "and never claim tests or tools ran unless the context proves it."
        ),
        llm,
    )

__all__ = [
    "create_repository_agent",
    "create_architecture_agent",
    "create_code_quality_agent",
    "create_documentation_agent",
    "create_security_agent",
    "create_risk_agent",
    "create_recommendation_agent",
    "create_summary_agent",
    "create_master_agent",
]