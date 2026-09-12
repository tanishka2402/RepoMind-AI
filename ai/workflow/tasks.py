"""
CrewAI tasks for RepoMind-AI.

The tasks are designed around evidence-first repository analysis.

Every analysis agent is instructed to:
- use only collected repository information
- provide explicit evidence
- avoid unsupported technology claims
- distinguish unavailable information from assumptions
"""

from crewai import Task


def _context(context_tasks):
    """Return CrewAI task context or an empty list."""
    return context_tasks or []


def create_repository_task(agent, repository_context):
    """Create the repository-analysis task."""

    return Task(
        description=f"""
Analyze the provided GitHub repository information.

Your job is to establish the factual foundation for the entire
RepoMind-AI analysis.

Use ONLY the repository context below.

Identify:

- Repository name
- Repository owner
- Description
- Default branch
- Languages
- Statistics
- Topics
- Actually collected files
- Actually collected source files
- Issues
- Pull requests
- Branches

IMPORTANT GROUNDING RULES:

1. Only report information that appears in the repository context.
2. Never invent files.
3. Never invent technologies.
4. Never invent frameworks.
5. Never invent dependencies.
6. Never invent features.
7. Never invent architecture.
8. Never invent vulnerabilities.
9. Never invent authentication or authorization.
10. Never invent databases.
11. Never invent dates.
12. If information is unavailable, say "Unavailable".
13. Do not assume that a technology exists because it is common
    for the type of repository.

For factual claims involving source files, identify the exact
file path.

Repository Context:

{repository_context}
""",
        expected_output="""
A concise factual repository overview.

Use this structure:

CATEGORY: Repository
TITLE: Repository Overview
SEVERITY: info
DESCRIPTION: factual overview
EVIDENCE: exact repository facts and file paths
RECOMMENDATION: N/A

Do not invent information.
""",
        agent=agent,
    )


def create_architecture_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the architecture-analysis task."""

    return Task(
        description=f"""
Analyze the architecture and structure of the repository.

Use ONLY:

1. The repository context below.
2. Findings produced by the previous repository task.

Evaluate:

- Project structure
- Major components
- Relationships between components
- Entry points
- Architectural patterns
- Architectural strengths
- Architectural weaknesses

IMPORTANT:

Do not assume a framework exists.

Do not assume a backend exists.

Do not assume a database exists.

Do not assume microservices exist.

Do not assume an API exists.

Do not assume a frontend framework exists.

A technology or architectural pattern may only be mentioned
if it is directly observable in the repository context.

Every finding MUST identify evidence.

Evidence should reference an exact file path whenever
the finding concerns source code.

For example:

CATEGORY: Architecture
TITLE: HTML page references a stylesheet
SEVERITY: info
DESCRIPTION: The main HTML page references a CSS stylesheet.
EVIDENCE: index.html contains a stylesheet reference to styles.css.
RECOMMENDATION: Keep shared styling organized in the stylesheet.

If architecture cannot be determined from the collected files,
say so explicitly.

Repository Context:

{repository_context}
""",
        expected_output="""
Structured architecture findings.

Each finding MUST contain:

CATEGORY:
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:

Evidence must refer to actual repository information.
""",
        agent=agent,
        context=_context(context_tasks),
    )


def create_code_quality_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the code-quality analysis task."""

    return Task(
        description=f"""
Analyze the code quality of the repository.

Use ONLY the repository context and previous findings.

Evaluate only code that was actually collected.

Consider:

- Organization
- Readability
- Maintainability
- Naming
- Duplication
- Error handling
- Complexity
- Consistency
- Technical debt
- HTML/CSS/JavaScript/Python/etc. quality only when
  those files are actually present

IMPORTANT:

Do not invent source files.

Do not invent functions.

Do not invent classes.

Do not invent tests.

Do not claim automated analysis was performed unless
the repository context explicitly proves it.

Do not claim a programming language exists unless the
repository context contains evidence for it.

Every finding MUST identify exact repository evidence.

If there is not enough source code to evaluate an area,
say:

"Insufficient collected source code to evaluate this area."

Repository Context:

{repository_context}
""",
        expected_output="""
Structured code-quality findings.

Each finding MUST contain:

CATEGORY: Code Quality
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:

Evidence must reference actual collected files whenever
the finding concerns source code.
""",
        agent=agent,
        context=_context(context_tasks),
    )


def create_documentation_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the documentation-analysis task."""

    return Task(
        description=f"""
Analyze the repository documentation.

Use ONLY the repository context and previous findings.

Evaluate:

- README quality
- Documentation coverage
- Setup instructions
- Usage instructions
- API/module documentation when observable
- Contributor guidance
- Missing documentation

IMPORTANT:

Do not invent setup instructions.

Do not invent API endpoints.

Do not invent installation commands.

Do not claim documentation is comprehensive unless the
collected documentation supports that conclusion.

Every important finding MUST include evidence.

If the available documentation is insufficient, say so.

Repository Context:

{repository_context}
""",
        expected_output="""
Structured documentation findings.

Each finding MUST contain:

CATEGORY: Documentation
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:
""",
        agent=agent,
        context=_context(context_tasks),
    )


def create_security_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the security-analysis task."""

    return Task(
        description=f"""
Analyze the repository for observable security concerns.

Use ONLY the repository context and previous findings.

Look for actual evidence of:

- Hardcoded secrets
- Unsafe configuration
- Authentication concerns
- Authorization concerns
- Unsafe input handling
- Dangerous command execution
- Sensitive information exposure
- Unsafe HTML or JavaScript behavior
- Dependency risks when dependencies are actually visible

IMPORTANT:

Do NOT claim that a security control exists unless you
can point to repository evidence.

Do NOT claim that authentication exists unless it is visible.

Do NOT claim that authorization exists unless it is visible.

Do NOT claim encryption exists unless it is visible.

Do NOT claim secure storage exists unless it is visible.

Do NOT claim a vulnerability exists without evidence.

Do NOT claim "no vulnerabilities" merely because no obvious
vulnerability was found.

Instead use language such as:

"No obvious security issue was identified in the collected
files, but the available source coverage is limited."

Every security finding MUST include evidence.

Repository Context:

{repository_context}
""",
        expected_output="""
Structured security findings.

Each finding MUST contain:

CATEGORY: Security
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:

Do not claim security controls that are not observable.
""",
        agent=agent,
        context=_context(context_tasks),
    )


def create_risk_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the risk-analysis task."""

    return Task(
        description=f"""
Identify and prioritize repository risks.

Use the findings from:

- Repository analysis
- Architecture analysis
- Code-quality analysis
- Documentation analysis
- Security analysis

IMPORTANT:

A risk must be connected to an observed finding.

Do not invent risks.

Do not assume production usage.

Do not assume sensitive data.

Do not assume users.

Do not assume authentication.

Do not assume a backend.

Do not assume a database.

Do not assume deployment infrastructure.

If a risk depends on information that is unavailable,
clearly identify that limitation.

For each risk provide:

CATEGORY: Risk
TITLE: short risk title
SEVERITY: info | low | medium | high | critical
DESCRIPTION: explanation
EVIDENCE: exact supporting repository evidence
RECOMMENDATION: practical risk-reduction action

Repository Context:

{repository_context}
""",
        expected_output="""
Structured prioritized risk findings.

Each finding MUST contain:

CATEGORY: Risk
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:

Every risk must be supported by previous findings.
""",
        agent=agent,
        context=_context(context_tasks),
    )


def create_recommendation_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the recommendation task."""

    return Task(
        description=f"""
Create practical recommendations based only on previous
repository findings.

Use:

- Architecture findings
- Code-quality findings
- Documentation findings
- Security findings
- Risk findings

Recommendations must be:

- Specific
- Practical
- Prioritized
- Evidence-based

IMPORTANT:

Do not recommend technologies that were not observed.

Do not recommend adding authentication unless a relevant
requirement or observed issue supports it.

Do not recommend adding a database unless repository evidence
supports the need.

Do not recommend changes merely because they are common
software-engineering practices.

Every recommendation MUST be connected to a previous finding.

Repository Context:

{repository_context}
""",
        expected_output="""
Structured prioritized recommendations.

Each recommendation MUST contain:

CATEGORY: Recommendation
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:
""",
        agent=agent,
        context=_context(context_tasks),
    )


def create_summary_task(
    agent,
    repository_context,
    context_tasks=None,
):
    """Create the final grounded synthesis task."""

    return Task(
        description=f"""
Create the final RepoMind-AI repository analysis report.

You are the final analysis summarizer.

You have access to:

1. The actual repository context.
2. Findings from the previous analysis agents.

Your job is to synthesize the findings.

DO NOT reproduce raw GitHub JSON.

DO NOT reproduce complete issue lists.

DO NOT reproduce complete pull-request lists.

DO NOT reproduce the entire repository context.

DO NOT invent technologies.

DO NOT invent frameworks.

DO NOT invent dependencies.

DO NOT invent architecture.

DO NOT invent databases.

DO NOT invent authentication.

DO NOT invent authorization.

DO NOT invent encryption.

DO NOT invent security controls.

DO NOT invent vulnerabilities.

DO NOT invent performance measurements.

DO NOT claim automated tools were run unless the evidence
shows that they were run.

The final report MUST use exactly these sections:

EXECUTIVE SUMMARY

REPOSITORY OVERVIEW

ARCHITECTURE FINDINGS

CODE QUALITY FINDINGS

DOCUMENTATION FINDINGS

SECURITY FINDINGS

RISK ASSESSMENT

RECOMMENDATIONS

For every important finding use:

CATEGORY:
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:

Allowed severity values:

critical
high
medium
low
info

GROUNDING RULES:

1. Every important claim must be supported by repository
   context or a previous agent finding.

2. Source-code findings must reference an actual collected
   file path.

3. Never infer a technology from general knowledge.

4. Never infer a framework from file extensions alone.

5. Never infer a database unless database evidence exists.

6. Never infer backend services unless backend evidence exists.

7. Never infer security controls unless security evidence exists.

8. If the available source code is too limited to evaluate
   something, explicitly state that.

9. Distinguish observed facts from AI analysis.

10. Keep the final report concise.

11. Do not output raw GitHub JSON.

12. Do not output raw PR data.

13. Do not output raw issue data.

14. Do not copy large source-code blocks.

15. Do not state that something was tested unless the repository
    context explicitly contains evidence of testing.

The actual repository context is:

{repository_context}
""",
        expected_output="""
A concise professional repository analysis.

The output MUST contain exactly:

EXECUTIVE SUMMARY

REPOSITORY OVERVIEW

ARCHITECTURE FINDINGS

CODE QUALITY FINDINGS

DOCUMENTATION FINDINGS

SECURITY FINDINGS

RISK ASSESSMENT

RECOMMENDATIONS

Each important finding must contain:

CATEGORY:
TITLE:
SEVERITY:
DESCRIPTION:
EVIDENCE:
RECOMMENDATION:

The report must be grounded in the supplied repository
context.

Unsupported claims must not be presented as facts.

Do not reproduce raw GitHub JSON.
""",
        agent=agent,
        context=_context(context_tasks),
    )

