### `README.md`

```markdown
# High-Throughput Async Web Scraping Engine

A resilient, production-ready distributed web scraping architecture built with Python. Designed to seamlessly bypass modern anti-bot protections, extract data concurrently, process workloads via b[...]

---

## Key Features

* **Hybrid Engine (`engine.py`):** 
  * High-speed HTTP fetches via `curl_cffi` using TLS fingerprint spoofing (`impersonate="chrome120").
  * Automatic fallback to headless Playwright browser automation with `playwright-stealth` for JavaScript-heavy targets.
  * Rapid C-based HTML parsing via `selectolax`.
* **Distributed Task Queue (`tasks.py` & `producer.py`):** 
  * Powered by `arq` and `Redis` for asynchronous, lock-free background job management.
* **Persistent Storage (`database.py`):** 
  * Async PostgreSQL integration using `SQLAlchemy 2.0` and `asyncpg` with built-in upsert (`INSERT ... ON CONFLICT`) logic.
* **Production-Ready Hygiene:** 
  * Strictly adheres to environment variable configs (`DATABASE_URL`, `REDIS_HOST`).
  * Full async context isolation preventing socket leaks and orphan browser processes.

---

## Directory Structure

```text
.
├── .gitignore          # Prevents tracking secrets, binaries, and virtual environments
├── README.md           # Documentation and pipeline architecture guide
├── backend/            # Core Python backend package (workers, engine, db)
│   ├── __init__.py
│   ├── database.py     # SQLAlchemy ORM models and PostgreSQL connection pool
│   ├── engine.py       # ProductionScraper class (curl_cffi + Playwright + Selectolax)
│   ├── producer.py     # Job dispatcher pushing URL scraping tasks into Redis
│   └── tasks.py        # arq worker definitions and execution handlers
├── frontend/           # Optional frontend UI (placeholder)
│   └── ScraperDashboard.jsx
└── requirements.txt    # Python dependencies
```

---

## Prerequisites & Installation

### 1. System Requirements

* Python 3.10+
* Docker & Docker Compose (recommended for running PostgreSQL and Redis)

### 2. Clone Repository & Environment Setup

```bash
git clone https://github.com/johntonye19-sudo/Scraper.git
cd Scraper

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser dependencies
playwright install chromium

```

---

## Getting Started

### Step 1: Start Infrastructure (Redis & PostgreSQL)

Run local instances using Docker:

```bash
# Start Redis
docker run -d --name redis-server -p 6379:6379 redis:alpine

# Start PostgreSQL
docker run -d --name postgres-server -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=scraper_db \
  postgres:alpine

```

### Step 2: Launch the Worker Process

In Terminal 1, run the `arq` queue worker daemon:

```bash
arq backend.tasks.WorkerSettings

```

### Step 3: Dispatch Scraping Jobs

In Terminal 2, execute the producer script to populate tasks into the queue:

```bash
python backend/producer.py

```

---

## Configuration & Environment Variables

The application fallbacks to standard local defaults, but accepts standard environment variables for production environments (Kubernetes, AWS, Heroku):

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL Async Connection String | `postgresql+asyncpg://postgres:postgres@localhost:5432/scraper_db` |
| `REDIS_HOST` | Host address for Redis queue | `localhost` |
| `REDIS_PORT` | Port for Redis queue | `6379` |

Example for running with custom environment variables:

```bash
export DATABASE_URL="postgresql+asyncpg://user:password@remote-db-host:5432/production_db"
export REDIS_HOST="redis-cluster.internal"
python backend/producer.py

```

---

## Verification & Error Handling

* **Automatic Engine Fallback:** If a fast static fetch (`curl_cffi`) returns an HTTP block or failure, the worker automatically re-routes the task to headless Playwright with stealth scripts ena[...]
* **Clean Shutdown Lifecycle:** Both workers (`backend.tasks`) and HTTP engines (`backend.engine`) explicitly close connection pools and browser instances upon execution end, preventing dangling browser ta[...]

---

## License

This project is open-source and available under the MIT License.
