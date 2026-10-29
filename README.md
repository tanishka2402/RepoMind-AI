# RepoMind-AI

RepoMind-AI analyzes public or accessible GitHub repositories and creates structured engineering reports. The application combines a FastAPI backend, an HTML/CSS/JavaScript dashboard, a CrewAI analysis workflow, deterministic repository insights, a static security scanner, SQLite persistence, and optional blockchain-backed report verification.

## Features

- Fetches repository metadata and source files through the GitHub API.
- Runs specialized CrewAI agents for architecture, code quality, documentation, security, risk, recommendations, and summaries.
- Builds repository context and intelligence, validates report content, and calculates structured scores.
- Scans fetched text files for potentially risky patterns, such as hardcoded credentials, unsafe deserialization, disabled TLS checks, and risky command execution. The scanner is heuristic: findings need human review, and repository code is not executed by the scanner.
- Supports account registration, login with JWTs, role-based access, saved analyses, history, dashboard metrics, and repository insights.
- Offers an architecture preview endpoint and dashboard view.
- Can register and verify a sanitized analysis summary with a configured Ethereum-compatible smart contract.

Blockchain support is optional. A locally calculated hash does not prove that a transaction reached a blockchain. On-chain registration requires a reachable RPC endpoint, a deployed compatible contract, a matching ABI, and a signing key. Keep full reports and source code off-chain.

## Architecture

```text
Browser dashboard (frontend/index.html)
               │ HTTP / JSON
               ▼
        FastAPI backend
        ├── Authentication and saved analyses (SQLite)
        ├── Architecture preview and dashboard insights
        └── AI analysis pipeline
             ├── GitHub repository fetcher
             ├── Repository context and static security scan
             ├── CrewAI agents with local Hugging Face inference
             └── Validation, structured report, and scoring
               │
               └── Optional Web3 service → compatible registry contract
```

## Technology

| Area | Stack |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| API | FastAPI, Uvicorn, Pydantic |
| AI workflow | CrewAI, Hugging Face Transformers, PyTorch |
| Default model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Repository data | GitHub API, PyGithub |
| Persistence and auth | SQLite, SQLAlchemy, JWT, Argon2 password hashing |
| Optional integrity layer | Web3.py, Ethereum-compatible RPC, Solidity registry |

## Repository layout

```text
ai/
  agents/                 Specialized analysis agents
  context/                Repository context and intelligence
  github_service/          GitHub API and repository fetching
  llm/                    Hugging Face inference and CrewAI adapter
  reports/                Validation, scoring, and report generation
  security/scanner.py     Static source-pattern scanner
  workflow/               Crew, tasks, and analysis pipeline
  requirements.txt        AI dependencies
backend/
  app/                    FastAPI routes, auth, database, insights, blockchain
  requirements.txt        API dependencies
  create_admin.py         Optional initial administrator setup
frontend/
  index.html              Browser dashboard
blockchain/blockchain/    Solidity registry and Hardhat project
database/                 Local SQLite database
```

## Requirements

- Python 3.10 or later and Git.
- GitHub access to the repositories being analyzed. A GitHub token is recommended for higher API limits and private repositories the token can access.
- Disk space and memory for the selected Hugging Face model. The default model downloads on first use.
- Node.js/npm only if you plan to build, deploy, or test the blockchain contracts.

On macOS, the model loader defaults to CPU. Set `HF_DEVICE=mps` to request Apple Metal inference; this may use substantial memory. You can choose another model with `HF_MODEL`.

## Setup

Run these commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt -r ai/requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the environment with `.venv\\Scripts\\Activate.ps1`.

Edit `.env` and set a unique `REPOMIND_JWT_SECRET`. Set `GITHUB_TOKEN` there for shared configuration. The AI GitHub client also reads `ai/.env`, which takes precedence for `GITHUB_TOKEN`; create that file if you prefer to keep the AI token separate. Do not commit either environment file or real credentials.

Environment variables:

| Variable | Use |
|---|---|
| `GITHUB_TOKEN` | Optional GitHub API credential; `ai/.env` overrides the root `.env` for the AI client |
| `REPOMIND_JWT_SECRET` | Secret used to sign access tokens; set a random, private value |
| `REPOMIND_ACCESS_TOKEN_MINUTES` | JWT lifetime in minutes; defaults to `60` |
| `HF_MODEL` | Hugging Face model identifier; defaults to `Qwen/Qwen2.5-1.5B-Instruct` |
| `HF_DEVICE` | Optional inference device: `cpu`, `mps`, or `cuda` |
| `ALLOW_MPS` | Set to `1` to use MPS automatically when `HF_DEVICE` is not set |
| `MAX_FILES` | Repository fetch limit, defaults to `2000` |
| `MAX_CONTRIBUTORS` | Contributor fetch limit, defaults to `100` |
| `REPOMIND_BLOCKCHAIN_RPC_URL` | Optional blockchain RPC endpoint |
| `REPOMIND_CONTRACT_ADDRESS` | Optional deployed registry address |
| `REPOMIND_BLOCKCHAIN_PRIVATE_KEY` | Optional signing key; use only a disposable test account for local development |
| `REPOMIND_ADMIN_USERNAME`, `REPOMIND_ADMIN_EMAIL`, `REPOMIND_ADMIN_PASSWORD` | Optional values for initial administrator creation |

The blockchain variables are only needed for chain registration and verification. The contract ABI must also be available where the blockchain client expects it.

## Run locally

Start the API in one terminal from the repository root:

```bash
source .venv/bin/activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend in a second terminal:

```bash
python3 -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open the dashboard at <http://127.0.0.1:5500>. The frontend is configured to call the API at `http://127.0.0.1:8000`. API docs are at <http://127.0.0.1:8000/docs>; the health endpoint is <http://127.0.0.1:8000/health>.

The backend creates required SQLite tables on startup in `database/repomind.db`. The first analysis may take longer while model files are downloaded and loaded.

## Authentication and API

Register or log in through the dashboard or API. The main authentication routes are:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

The analysis and dashboard routes require a bearer token. The API also exposes:

| Route | Purpose |
|---|---|
| `POST /analyze` | Analyze a GitHub repository and save the result for the signed-in user |
| `POST /architecture-preview` | Generate a repository architecture preview |
| `GET /analyses` | List the signed-in user's saved analyses |
| `GET /analyses/{analysis_id}` | Retrieve an authorized saved analysis |
| `GET /analyses/{analysis_id}/structured` | Retrieve structured analysis data |
| `GET /analyses/{analysis_id}/insights` | Retrieve repository insights |
| `GET /analyses/{analysis_id}/verify` | Verify the saved summary against blockchain data when configured |
| `GET /dashboard` | Retrieve dashboard statistics |
| `GET /admin/users` | Administrator-only user listing |

Use `/docs` as the live source of truth for request and response schemas. Protected routes expect `Authorization: Bearer <access_token>`. Registration creates a standard user. To create the initial administrator, set the `REPOMIND_ADMIN_*` variables and run:

```bash
python backend/create_admin.py
```

## Blockchain development

The Hardhat project is in `blockchain/blockchain/`. Its scripts include registry deployment and a basic integration script. Review that project's README and configuration before running blockchain commands. Use a local chain or test network and a disposable account. A successful analysis does not guarantee successful on-chain registration; check the API result and backend logs for transaction status and hash.

## Troubleshooting

- **Frontend cannot reach the API:** Confirm both servers are running, the API is on port `8000`, and the frontend is served from port `5500`. Check the browser console and backend logs.
- **GitHub rate limit or authentication error:** Set a valid `GITHUB_TOKEN` in `.env` or `ai/.env`; confirm it can access the requested repository.
- **Model loading is slow or runs out of memory:** Wait for the first model download, select a smaller compatible model with `HF_MODEL`, or use `HF_DEVICE=cpu`. MPS can require significant memory.
- **401 response:** Log in again and use a current bearer token.
- **403 response:** Confirm the account owns the analysis or has the required administrator role.
- **Blockchain unavailable:** Analysis can run without blockchain configuration. Check RPC access, contract address, ABI compatibility, and backend environment settings if verification is needed.

## Security and data

- Keep GitHub tokens, JWT secrets, passwords, and blockchain private keys out of source control.
- The SQLite database contains account and analysis data. Treat it as local application data and do not publish it.
- Repository files and AI output are untrusted input. The static scanner reports patterns for review; it is not a guarantee that a repository is safe.
- Blockchain records should contain only a sanitized integrity summary. Do not publish full reports, source files, credentials, or personal data on-chain.

## License

See [LICENSE](LICENSE).
