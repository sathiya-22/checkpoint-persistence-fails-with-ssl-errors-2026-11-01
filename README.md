# LangGraph PostgreSQL Checkpoint Persistence SSL Fix

## The Real Problem and Who It Affects
Developers building agentic AI systems often rely on state persistence mechanisms to ensure their agents can resume operations from a known state, even across restarts or failures. LangGraph, a popular library for building stateful agent applications, offers PostgreSQL as a robust option for checkpointing. However, a common and critical issue observed in the community is the occurrence of SSL errors (e.g., 'bad length') when LangGraph attempts to send queries and parameters to a PostgreSQL database configured with SSL. This problem directly leads to unreliable state persistence, data loss, and operational instability for agentic systems, hindering their robustness and production readiness.

This project specifically targets developers using LangGraph with PostgreSQL for checkpointing, especially those deploying in environments where SSL/TLS is mandated or preferred for database connections.

## Why This Project Shape/Stack Was Chosen
The problem lies in the interaction between the Python PostgreSQL driver (psycopg2 or psycopg3) and the underlying SSL library (OpenSSL) when specific SSL parameters are used or implicitly assumed by the PostgreSQL server. Instead of attempting to patch LangGraph or the database driver directly, which can be complex and brittle, this prototype provides a **minimal Python utility** that demonstrates how to configure the PostgreSQL connection *correctly* to avoid these SSL errors.

The chosen approach focuses on:
1.  **Direct Problem Addressing**: Pinpointing the `sslmode` and `sslrootcert` parameters as common culprits and showing their correct usage.
2.  **Simplicity and Portability**: A self-contained Python script is easy to understand, run, and integrate into existing LangGraph projects. It requires minimal dependencies beyond what LangGraph already uses for PostgreSQL.
3.  **No LLM Involvement**: The problem is purely infrastructural (database connectivity), so no LLM integration is necessary or provided. This keeps the focus squarely on the SSL issue.
4.  **Fixture-based Demonstration**: We use a simple LangGraph "agent" and mock data to demonstrate checkpointing without needing an actual LLM API key, making it immediately runnable.

## Setup and Usage Instructions (Zero API Keys)

### Prerequisites
*   Python 3.8+
*   Docker (for easily running a PostgreSQL instance with SSL)

### 1. Set up PostgreSQL with SSL (using Docker)
This project includes a `docker-compose.yml` to spin up a PostgreSQL instance with self-signed SSL certificates, mimicking a common setup where these issues arise.

```bash
docker-compose up -d
```
This command will:
*   Start a PostgreSQL container.
*   Generate self-signed SSL certificates for the database.
*   Configure PostgreSQL to use SSL, requiring client certificates.

You can verify the database is running and accessible:
```bash
docker logs pg-ssl-db
```
Look for lines indicating PostgreSQL is ready and listening for SSL connections.

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Prototype
The `main.py` script will attempt to run a simple LangGraph agent, checkpointing its state to the PostgreSQL database. It's configured to use the `sslmode='require'` and point to the generated `root.crt` for server certificate verification.

```bash
python main.py
```

**Expected Output:**
You should see output indicating the agent's steps and successful checkpointing, without any SSL 'bad length' or similar errors. For example:
```
--- Initial Agent State ---
{'agent_state': 'initial'}
--- Agent Step 1 ---
{'agent_state': 'step_1'}
Checkpoint saved successfully.
--- Agent Step 2 (Restored from checkpoint) ---
{'agent_state': 'step_2'}
Checkpoint saved successfully.
--- Final Agent State ---
{'agent_state': 'step_2'}
```

### 4. Clean Up
To stop and remove the PostgreSQL container:
```bash
docker-compose down -v
```
This will also remove the generated certificates and database volume.

## Optional Real-LLM Adapter
This project addresses a pure infrastructure problem (database connectivity) and does not involve LLMs directly. Therefore, no optional real-LLM adapter is provided or necessary. The core logic of correctly configuring PostgreSQL SSL for LangGraph checkpointing stands alone.
