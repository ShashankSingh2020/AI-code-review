# 🔍 AI Code Review + Repository Analyst

An automated code-review pipeline that clones a public GitHub repository into a sandbox, runs **deterministic static analysis** on it (Ruff, Radon, Python AST), maps its **import/dependency graph**, and then asks an LLM (Google Gemini) to write an **evidence-grounded** health report, based only on what the analyzers actually found.

> **Why this design?** Asking an LLM to "review my code" directly leads to vague or hallucinated feedback. Here the analyzers produce hard evidence first (file, line, rule, complexity score), and the LLM only *summarises and prioritises* that evidence. Every claim in the final review can be traced back to a real finding.

---

## 📑 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [How the Analysis Works](#-how-the-analysis-works)
- [Sandbox & Safety Limits](#-sandbox--safety-limits)
- [LLM Providers](#-llm-providers)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Shallow-clone ingestion** | Clones only the requested branch with `--depth 1`, enforcing timeout, file-count and size limits so a hostile or huge repo can't exhaust the server. |
| **Static analysis (Ruff)** | Lint errors, likely runtime hazards and common security smells, reported with file, line and rule code. |
| **AST analysis** | Native Python `ast` parsing flags dangerous constructs such as `eval()` and bare `except:` blocks. |
| **Cyclomatic complexity (Radon)** | Per-function complexity scores to find the hardest-to-maintain code. |
| **Dependency graph** | Traverses imports across modules to build an architectural map showing coupling and hotspots. |
| **AI review synthesis** | Gemini turns raw findings into an executive-style code-health review, with an **offline mock fallback** so the project runs with no API key. |
| **Async persistence** | Results are stored in PostgreSQL (Neon) via SQLAlchemy 2.0 + asyncpg, so past analyses can be retrieved. |
| **Web UI** | Tailwind-styled frontend for submitting a repository and viewing the report. |

---

## 🏗 Architecture

```mermaid
flowchart LR
    U[User / Frontend] -->|Repo URL + branch| API[FastAPI]
    API --> CL[Sandboxed shallow clone]
    CL --> RUFF[Ruff<br/>lint & security]
    CL --> AST[AST scanner<br/>eval, bare except]
    CL --> RAD[Radon<br/>cyclomatic complexity]
    CL --> DEP[Import graph builder]
    RUFF --> EV[(Evidence bundle)]
    AST --> EV
    RAD --> EV
    DEP --> EV
    EV --> LLM{LLM provider}
    LLM -->|gemini| G[Gemini 1.5 Flash]
    LLM -->|mock| M[Offline mock reviewer]
    G --> REP[Final review]
    M --> REP
    REP --> DB[(PostgreSQL / Neon)]
    DB --> API
    API --> U
```

**Pipeline stages**

1. **Ingest**: validate the URL, shallow-clone into `storage/temp_repos`, enforce size/file limits.
2. **Analyze**: run Ruff, the AST scanner, Radon and the dependency-graph builder.
3. **Aggregate**: merge all findings into one structured evidence bundle.
4. **Synthesize**: send the evidence (not the raw repo) to the LLM for a written review.
5. **Persist & serve**: store the result in PostgreSQL and return it to the UI/API.
6. **Cleanup**: delete the temporary clone.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic v2, pydantic-settings |
| Database | PostgreSQL (Neon Cloud), SQLAlchemy 2.0 (async), asyncpg |
| Static analysis | Ruff, Radon, Python `ast` module |
| AI | Google Generative AI SDK (Gemini 1.5 Flash) or built-in mock provider |
| HTTP client | httpx |
| Frontend | Tailwind CSS |

---

## 📁 Project Structure

```
AI-code-review/
├── app/                     # FastAPI backend (API routes, analyzers, services, models)
├── frontend/                # Web UI (Tailwind CSS)
├── storage/
│   └── temp_repos/          # Temporary sandbox for cloned repositories
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── tailwind.config.js       # Tailwind configuration
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- **Git** installed and available on your `PATH`
- A PostgreSQL database (a free [Neon](https://neon.tech) project works well)
- *(Optional)* A [Google AI Studio](https://aistudio.google.com/) API key for Gemini

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ShashankSingh2020/AI-code-review.git
cd AI-code-review

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env (see Configuration below)

# 5. Run the server
uvicorn app.main:app --reload
```

The API will be available at **http://127.0.0.1:8000** and the interactive docs at **http://127.0.0.1:8000/docs**.

> ⚠️ Adjust `app.main:app` if your entry point lives elsewhere.

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and set the values below.

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment. |
| `APP_DEBUG` | `true` | Enables debug behaviour. Set to `false` in production. |
| `API_V1_STR` | `/api/v1` | URL prefix for all API routes. |
| `PROJECT_NAME` | `AI Code Review + GitHub Repository Analyst` | Title shown in the API docs. |
| `DATABASE_URL` | — | Async PostgreSQL URL, e.g. `postgresql+asyncpg://USER:PASSWORD@HOST/DB?ssl=require`. |
| `MAX_REPO_SIZE_MB` | `50` | Reject repositories larger than this. |
| `MAX_REPO_FILES` | `500` | Reject repositories with more files than this. |
| `MAX_SINGLE_FILE_BYTES` | `512000` | Skip individual files larger than ~500 KB. |
| `CLONE_TIMEOUT_SECONDS` | `45` | Abort cloning after this many seconds. |
| `PIPELINE_TIMEOUT_SECONDS` | `300` | Abort the whole analysis after this many seconds. |
| `TEMP_STORAGE_PATH` | `./storage/temp_repos` | Where temporary clones are stored. |
| `LLM_PROVIDER` | `mock` | `mock` (offline) or `gemini`. |
| `GEMINI_API_KEY` | — | Required only when `LLM_PROVIDER=gemini`. |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use. |

> 🔒 **Never commit your real `.env`.** It contains your database password and API key.

---

## 🧪 Usage

### Through the web UI

1. Start the backend (see above) and open the frontend.
2. Paste a public GitHub repository URL and choose a branch.
3. Submit and wait for the pipeline to finish.
4. Read the report: findings, complexity hotspots, dependency map and the AI summary.

### Through the API

Open **`/docs`** (Swagger UI) to explore and try every endpoint. A typical request looks like this:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/<analyze-endpoint> \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/<owner>/<repo>", "branch": "main"}'
```

> ✏️ Replace `<analyze-endpoint>` and the request body with the actual route and schema from your code.

### Example output (illustrative)

```json
{
  "repo": "owner/repo",
  "summary": {
    "files_analyzed": 42,
    "lint_issues": 18,
    "security_flags": 3,
    "avg_complexity": 4.7,
    "max_complexity": 23
  },
  "ai_review": "The codebase is generally well structured, but three functions exceed a complexity of 15 ..."
}
```

---

## 🔬 How the Analysis Works

**Ruff (lint, runtime hazards, security)**
Runs a curated rule set and returns structured findings (rule code, message, file, line). It is fast and fully deterministic, so the same code always gives the same result.

**AST scanner**
Parses each `.py` file into a syntax tree and walks it looking for risky patterns such as `eval()` and bare `except:` clauses. Because it inspects the tree rather than the text, it avoids false positives from comments and strings.

**Radon (cyclomatic complexity)**
Scores each function. Higher numbers mean more branching paths and harder code to test and maintain; the highest-scoring functions are surfaced as refactoring candidates.

**Dependency graph**
Resolves `import` statements between modules into a directed graph, showing which modules everything depends on and where tight coupling or circular imports exist.

**Evidence-grounded AI synthesis**
Only the aggregated findings are passed to the LLM, with instructions to cite them. This keeps the review factual and limits hallucination. If no API key is set (or `LLM_PROVIDER=mock`), a deterministic mock reviewer produces the summary, so the project always works offline.

---

## 🛡 Sandbox & Safety Limits

Analysing untrusted repositories is risky, so the pipeline is defensive by design:

- **Static analysis only.** Cloned code is *never executed or imported*.
- **Shallow clone** (single branch, `--depth 1`) to minimise download size.
- **Hard limits** on repo size, file count, individual file size, clone time and total pipeline time.
- **Temporary storage** that is cleaned up after each run.
- **Secrets stay out of the repo:** configuration is loaded from environment variables.

---

## 🤖 LLM Providers

| Provider | Setting | Notes |
|---|---|---|
| **Mock** | `LLM_PROVIDER=mock` | Default. No API key, no network, ideal for development and demos. |
| **Gemini** | `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` | Higher-quality natural-language review via Gemini 1.5 Flash. |

---

## 🗺 Roadmap

- [ ] Support JavaScript/TypeScript analysis (ESLint, complexity tools)
- [ ] Docker + `docker-compose` for one-command setup
- [ ] GitHub Actions CI (lint + tests)
- [ ] Unit and integration tests with coverage badge
- [ ] Interactive dependency-graph visualisation in the UI
- [ ] Authentication and per-user report history
- [ ] Private-repo support via GitHub OAuth
- [ ] Rate limiting and background job queue
- [ ] Provider abstraction for other LLMs (OpenAI, Claude, local models)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

Add a license of your choice (MIT is a common default for portfolio projects) and reference it here.

---

## 👤 Author

**Shashank Pratap Singh**

- GitHub: [@ShashankSingh2020](https://github.com/ShashankSingh2020)
- LinkedIn: [shashank-pratap-singh](https://linkedin.com/in/shashank-pratap-singh-530437303)
- Email: singh2020shashank@gmail.com

⭐ If you find this project useful, consider giving it a star!
