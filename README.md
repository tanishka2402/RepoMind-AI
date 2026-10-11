# RepoMind-AI

**An agentic GitHub repository analyzer built with CrewAI, FastAPI, a local LLM, and blockchain-backed integrity verification.**

RepoMind-AI turns a GitHub repository into a structured engineering report. It combines repository data collection, specialized AI agents, evidence-grounded validation, deterministic scoring, authenticated report history, and an optional Ethereum-compatible blockchain integrity layer.

> **Important:** Blockchain registration depends on a reachable RPC endpoint, a deployed compatible smart contract, a matching contract ABI/address, and a configured signing key. A successful local hash calculation alone does not prove that a blockchain transaction was recorded.

## Contents

- [Highlights](#highlights)
- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Run the application](#run-the-application)
- [API and authentication](#api-and-authentication)
- [Blockchain integrity verification](#blockchain-integrity-verification)
- [Troubleshooting](#troubleshooting)
- [Security notes](#security-notes)
- [Future improvements](#future-improvements)

## Highlights

- **GitHub repository analysis:** Collects repository information through the GitHub API.
- **CrewAI multi-agent workflow:** Specialized roles cover architecture, code quality, documentation, security, risk, recommendations, and summary generation.
- **Local LLM inference:** The project is designed to use a locally hosted Qwen2.5-1.5B-Instruct model; Apple MPS is noted in the project configuration.
- **Evidence-grounded reports:** Builds repository context and validates report content against available repository evidence to reduce unsupported conclusions.
- **Structured scoring:** Produces analysis categories, overall scoring, risks, and recommendations.
- **FastAPI backend:** REST endpoints for analysis, saved history, structured results, and verification.
- **Persistence:** SQLite and SQLAlchemy store users and saved analysis data.
- **Authentication and authorization:** JWT-based authentication, password hashing, roles, and ownership checks.
- **Blockchain integrity layer:** Web3.py integration can register selected analysis-summary integrity data with a compatible smart contract and verify it later when configured.
- **Dashboard:** HTML/JavaScript frontend for submitting repositories and viewing results and history.

## How it works

1. A user signs in and submits a GitHub repository URL.
2. The backend retrieves repository data through the GitHub API.
3. A context-building layer organizes relevant repository evidence.
4. CrewAI coordinates specialized agents to inspect the repository.
5. The report is structured and validated against collected evidence.
6. Scoring, risks, and recommendations are finalized.
7. The analysis is saved in SQLite and made available in the dashboard/history.
8. When blockchain configuration is available, the application can register a sanitized summary or integrity proof.
9. A verification request reconstructs the expected summary and compares it with the blockchain record.

The full analysis report and sensitive application data should remain off-chain. The blockchain layer is intended for integrity verification, not as the primary report database.

## Architecture

```text
Browser dashboard (HTML / JavaScript)
                 |
                 v
          FastAPI REST API
                 |
       +---------+----------+
       |         |          |
       v         v          v
 GitHub API   SQLite DB   Blockchain service
       |                    |
       v                    v
 Repository context      Web3.py / RPC
       |                    |
       v                    v
 CrewAI agents         Smart contract
       |
       v
 Grounding, validation, scoring
       |
       v
 Structured report and recommendations
```

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI, Uvicorn |
| AI orchestration | CrewAI |
| Local model | Qwen2.5-1.5B-Instruct (project configuration) |
| Repository data | GitHub API |
| Database | SQLite, SQLAlchemy |
| Authentication | JWT, password hashing |
| Blockchain integration | Web3.py, Solidity smart contract, Ethereum-compatible RPC |
| Integrity | SHA-256 / canonicalized report data |

## Repository layout

The exact tree may evolve, but these are the main modules referenced by the project:

```text
RepoMind-AI/
├── ai/
│   ├── context/
│   │   └── repository_intelligence.py
│   └── llm/
│       └── inference.py
├── backend/
│   ├── app/
│   │   ├── blockchain/
│   │   │   ├── client.py
│   │   │   ├── hasher.py
│   │   │   └── service.py
│   │   ├── main.py
│   │   └── schemas.py
│   └── requirements.txt
├── frontend/
│   └── index.html
└── README.md
```

Other modules, migrations, smart-contract files, model files, and configuration files may be present in your checkout.

## Prerequisites

- Python compatible with the project's installed dependencies.
- Git.
- Access to the GitHub repositories you want to analyze.
- The local model and model runtime required by the current AI configuration.
- Optional for blockchain: an Ethereum-compatible RPC endpoint, deployed compatible contract, contract ABI, and a funded signing account on the selected network.

The project may use Apple MPS for local inference on supported Apple hardware. If your machine does not support MPS, check the inference implementation and configure a supported device.

## Setup

### 1. Clone or open the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd RepoMind-AI
```

If the repository is already on your machine, simply `cd` into its directory.

### 2. Create and activate a virtual environment

Use the environment already established for the project if available. A standard alternative is:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

The AI components may have their own dependency setup. Review the `ai/` directory and current project configuration before installing additional packages. Avoid mixing incompatible virtual environments.

### 4. Configure local settings

Create the environment file expected by your application configuration. It is commonly `.env` at the project root, but check how the code loads environment variables. See [Configuration](#configuration).

Never commit API tokens, JWT secrets, or blockchain private keys.

### 5. Start the backend

From the repository root:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug
```

Keep this terminal running. Activate the correct Python environment first.

### 6. Open API documentation

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

Use the login endpoint documented by the running application to obtain an access token. In Swagger, click **Authorize** and provide the token in the format requested by the dialog before calling protected endpoints.

### 7. Open the frontend

Open `frontend/index.html` in your browser if the frontend is configured for direct local use. If it is served by a local web server, use that server's URL.

The frontend must point to the correct backend base URL. If requests fail, check the API URL, browser console, CORS configuration, and backend logs.

## Configuration

These variable names are used by the blockchain client. Confirm the environment-loading behavior in your current code before deciding where to put them.

| Variable | Purpose |
|---|---|
| `REPOMIND_BLOCKCHAIN_RPC_URL` | RPC URL for the selected Ethereum-compatible network |
| `REPOMIND_CONTRACT_ADDRESS` | Address of the deployed registry contract |
| `REPOMIND_BLOCKCHAIN_PRIVATE_KEY` | Private key used to sign registration transactions |

Example placeholders (replace locally; do not commit real values):

```dotenv
REPOMIND_BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
REPOMIND_CONTRACT_ADDRESS=0xYourDeployedContractAddress
REPOMIND_BLOCKCHAIN_PRIVATE_KEY=YOUR_LOCAL_TEST_PRIVATE_KEY
```

These are examples, not working credentials or a guarantee that a contract is deployed at that address. The contract ABI must also match the deployed contract and be available at the path expected by `backend/app/blockchain/client.py`.

For local development, use a disposable test account and a local/test network. Never use a wallet holding valuable assets for development.

## Run the application

1. Activate the correct Python environment.
2. Start the backend using the Uvicorn command above.
3. Confirm the API is available at `http://127.0.0.1:8000/docs`.
4. Register or sign in through the API/frontend.
5. Submit a GitHub repository and wait for the analysis to complete.
6. Review the report and saved analysis history.
7. If blockchain is configured, inspect the analysis response and backend logs for registration status and transaction metadata.
8. Use the verification endpoint for a saved analysis you are authorized to access.

## API and authentication

The exact endpoints depend on the version running locally. Use `/docs` as the source of truth. The project code includes an endpoint with this shape:

```http
GET /analyses/{analysis_id}/verify
```

It requires authentication and checks whether the current user owns the analysis or has an administrator role. In Swagger:

1. Call the login endpoint and obtain an access token.
2. Click **Authorize** and enter the token as requested.
3. Call the verification endpoint with an analysis ID belonging to your account, or use an administrator account.
4. Inspect response fields such as `verified`, `status`, and `message`.

A `401 Unauthorized` response such as `{"detail":"Authentication required."}` means the request needs authorization; it is not a blockchain verification result. A `403 Forbidden` response indicates an access-permission problem.

## Blockchain integrity verification

The blockchain feature is intended to provide tamper-evident integrity verification for a sanitized analysis summary.

### What a successful test should establish

- The backend can connect to the configured RPC endpoint.
- The contract address is valid and the contract ABI matches the deployed contract.
- A registration transaction is submitted and receives a successful receipt.
- The transaction hash and associated analysis identifier are available for inspection.
- Verification reads the expected record from the chain and compares it with the reconstructed report summary.
- A controlled tampering test causes verification to report a mismatch.

### Suggested manual test

1. Configure a local or test network and deploy the compatible registry contract.
2. Confirm the RPC URL, contract address, ABI, and test signing key are configured correctly.
3. Run a new analysis.
4. Inspect the backend log and analysis response for registration status, transaction hash, and contract address.
5. Call `GET /analyses/{analysis_id}/verify` with an authenticated user who owns the analysis.
6. Confirm that an unchanged report verifies successfully.
7. In a disposable test environment only, alter a copy of stored report data and verify that the integrity check detects the difference.
8. If using a public testnet, look up the transaction hash on the explorer for that specific network.

A hash stored only in SQLite is not evidence that a transaction was written on-chain. A successful transaction receipt proves execution, but the application should still verify that the correct contract and record were used.

## Troubleshooting

### `401 Unauthorized` / `Authentication required`

Authorize Swagger with a valid access token, then retry the protected endpoint.

### `403 Forbidden`

Check that the analysis belongs to the signed-in user or use an authorized administrator account.

### Blockchain RPC connection failure

- Confirm the RPC URL is reachable.
- Check that the local node or development chain is running, if applicable.
- Confirm the environment variable is loaded by the backend process.
- Restart FastAPI after changing environment configuration.

### Contract or ABI error

- Confirm the contract is deployed on the network selected by the RPC URL.
- Check the contract address and checksum formatting.
- Ensure the ABI loaded by the client matches the deployed contract.
- Confirm that the contract exposes the functions expected by the client, such as registration, retrieval, and verification.

### Registration fails but analysis completes

The application may handle blockchain registration errors separately from the main analysis flow. Check backend logs and the response's blockchain status rather than assuming a completed analysis means on-chain registration succeeded.

### Local LLM fails to initialize

- Confirm the model files are available at the configured location.
- Check the Python environment and installed model dependencies.
- Review `ai/llm/inference.py` and backend logs.
- Check whether the configured device (for example, Apple MPS) is supported by your machine and PyTorch build.

### Frontend cannot reach the backend

- Confirm Uvicorn is running on the expected host and port.
- Check the frontend's API base URL.
- Inspect the browser developer console and backend logs.
- Check CORS settings if frontend and backend use different origins.

## Security notes

- Never commit `.env` files, private keys, JWT secrets, passwords, or GitHub access tokens.
- Keep full reports, repository source code, and user data off-chain unless there is a deliberate, reviewed reason otherwise.
- Use test accounts and test networks for development.
- Enforce authentication and ownership checks on analysis, history, report, and verification endpoints.
- Treat repository content and model output as untrusted input; validate and sanitize before rendering or persisting.
- Do not expose detailed internal exceptions to untrusted clients in production.
- A blockchain record makes the recorded value tamper-evident; it does not guarantee the original analysis was correct or every AI conclusion is true.

## Future improvements

Potential next steps include:

- Automated integration tests for registration and verification.
- Clear UI states for pending, successful, failed, and unavailable blockchain registration.
- Transaction links for supported public test networks.
- More comprehensive language and dependency analysis.
- CI/CD and pull-request integration.
- Cloud deployment and continuous repository monitoring.
- Improved setup scripts and configuration validation.

## Contributing

1. Create a feature branch.
2. Keep changes focused and add tests for behavior changes.
3. Never commit secrets, model weights, virtual environments, or local databases.
4. Document new environment variables and setup steps.
5. Open a pull request with a concise explanation and test results.

## License

No license information was provided. Add a `LICENSE` file and update this section before publishing if you intend to grant reuse rights.
