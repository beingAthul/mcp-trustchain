# MCP-Trustchain

> **Deterministic, rule-based cybersecurity enforcement for Model Context Protocol (MCP) tool configurations.**

MCP-Trustchain is a security enforcement system that protects AI agent ecosystems by statically scanning, approving, and continuously verifying the integrity of MCP tool configuration files. It prevents tool poisoning, unauthorized modifications, and insecure configurations before any tool is ever executed.

---

##  What It Does

Modern AI agents rely on MCP servers to invoke external tools. A compromised or maliciously crafted `mcp.json` configuration can expose systems to remote code execution, credential theft, data exfiltration, and privilege escalation.

MCP-Trustchain solves this by enforcing a strict **Scan → Approve → Verify** lifecycle:

1. **Scan** — Performs static analysis on a tool config, flagging dangerous patterns (RCE, credential exposure, path traversal, auto-approval bypass, data exfiltration combinations).
2. **Approve** — An administrator explicitly approves a clean config. A canonical SHA-256 hash is computed and stored as the trusted baseline.
3. **Verify** — Before every tool execution, the client submits its current config. The system re-hashes it and compares it to the approved baseline. Any deviation results in a `BLOCK` decision and is logged as a potential tool poisoning event.

All decisions are recorded in a tamper-evident **audit log** with timestamps and reasoning.

---

##  Features

| Feature | Description |
|---|---|
| **Static Rule Engine** | YAML-based rules detect RCE, credential leaks, path traversal, and more |
| **Dangerous Combination Detection** | Identifies risky capability pairings (e.g., `read_file` + `network_send`) |
| **Canonical SHA-256 Integrity Hashing** | Deterministic hashing ensures config order doesn't affect verification |
| **Tool Lifecycle Management** | Tracks `APPROVED`, `BLOCKED`, `MODIFIED`, and `RE-APPROVED` states |
| **Real-time Audit Logging** | Every action (scan, approve, verify, block) is logged with context |
| **Web Dashboard** | Professional UI for registry management, verification, and audit review |
| **REST API** | Full API for programmatic integration with MCP clients |
| **Client Simulator** | CLI tool to simulate MCP client verification requests |

---

## Architecture

```
mcp-trustchain/
├── app/
│   ├── main.py              # FastAPI application entrypoint
│   ├── db.py                # SQLite database layer (tools + audit log)
│   ├── api/
│   │   └── routes.py        # REST API endpoints
│   ├── core/
│   │   ├── scanner.py       # Static analysis engine
│   │   ├── integrity.py     # SHA-256 canonical hashing
│   │   └── rules.yaml       # Security rule definitions
│   ├── web/
│   │   └── views.py         # Web UI route handlers
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, and static assets
├── client_sim/
│   ├── mcp_client.py        # CLI-based MCP client simulator
│   ├── safe_tool.json       # Example: safe configuration
│   ├── compromised_rce.json # Example: RCE attack vector
│   └── compromised_combo.json # Example: data exfiltration combo
├── data/
│   └── trustchain.db        # SQLite database (auto-created)
├── tests/                   # Test suite
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- `pip` package manager

### Installation

```powershell
# 1. Clone the repository
git clone https://github.com/your-username/mcp-trustchain.git
cd mcp-trustchain

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the Application

```powershell
# Start the development server (API + Web UI on the same server)
python -m app.main
```

The application will be available at **http://localhost:8000**

> **Note:** The SQLite database is auto-created at `data/trustchain.db` on first launch.

### Stopping the Application

Press **`Ctrl + C`** in the terminal to stop the server. To exit the virtual environment:

```powershell
deactivate
```

---

## Web Interface

| Page | URL | Description |
|---|---|---|
| **Dashboard / Scan** | `http://localhost:8000/` | Paste & scan MCP configs for security issues |
| **Tool Registry** | `http://localhost:8000/registry` | View and manage approved/blocked tools |
| **Verify Config** | `http://localhost:8000/verify` | Manually verify a config against its approved hash |
| **Audit Log** | `http://localhost:8000/audit` | Review the full tamper-evident audit trail |

---

## 🔌 REST API Reference

All API endpoints are prefixed with `/api/v1`.

### `POST /api/v1/scan`
Scans a raw MCP configuration JSON for security issues. No authentication or registration needed.

**Request Body:** Any valid MCP config JSON object.

**Response:**
```json
{
  "status": "success",
  "severity": "CRITICAL",
  "is_safe": false,
  "findings": [
    {
      "rule_id": "R002",
      "risk_type": "Remote Code Execution (RCE)",
      "severity": "CRITICAL",
      "explanation": "Detects potentially dangerous system command execution capabilities (Matched: 'bash')",
      "suggested_fix": "Restrict command execution capabilities..."
    }
  ]
}
```

### `POST /api/v1/approve`
Approves a tool config, computing and storing its canonical hash as the trusted baseline.

**Request Body:**
```json
{
  "tool_id": "git-tool-v1",
  "name": "Git Status Tool",
  "config": { ... }
}
```

### `POST /api/v1/verify`
Verifies the integrity of a tool config before execution. Returns `ALLOW` or `BLOCK`.

**Request Body:**
```json
{
  "tool_id": "git-tool-v1",
  "config": { ... }
}
```

**Response:**
```json
{
  "decision": "ALLOW",
  "reason": "Integrity validated. Configuration is unmodified.",
  "match": true,
  "current_hash": "a3f9...",
  "expected_hash": "a3f9..."
}
```

### `POST /api/v1/block`
Manually blocks a registered tool, preventing future executions.

### `POST /api/v1/reverify`
Re-approves a `MODIFIED` tool with a new trusted hash baseline.

### `GET /api/v1/tools`
Returns all registered tools and their current status.

### `GET /api/v1/audit`
Returns the last 100 audit log entries, ordered by most recent.

---

## Client Simulator

The `client_sim/` directory contains a CLI tool and sample configs to test the full verification workflow.

```powershell
# Run the simulator with a safe configuration
python client_sim/mcp_client.py client_sim/safe_tool.json git-tool-v1

# Simulate an attack with an RCE-compromised config
python client_sim/mcp_client.py client_sim/compromised_rce.json git-tool-v1
```

> **Note:** The tool must be approved first via the `/api/v1/approve` endpoint before verification will pass.

---

## Security Rules

Rules are defined in `app/core/rules.yaml` and can be extended without touching the application code.

| Rule ID | Name | Severity | Detects |
|---|---|---|---|
| `R001` | Hardcoded Credentials | `HIGH` | `api_key`, `secret`, `password`, `token` |
| `R002` | Command Execution Exposure | `CRITICAL` | `bash`, `exec`, `powershell`, `os.system` |
| `R003` | Path Traversal | `HIGH` | `../`, `/etc/`, `C:\Windows`, `/root` |
| `R004` | Automatic Approval Flags | `MEDIUM` | `auto_approve`, `always_allow` |
| `C001` | Data Exfiltration Risk | `CRITICAL` | `read_file` + `network_send` combo |

---

## Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Templating:** [Jinja2](https://jinja.palletsprojects.com/)
- **Database:** SQLite (via Python's built-in `sqlite3`)
- **Hashing:** SHA-256 via Python's `hashlib`
- **Config:** YAML rule definitions via `PyYAML`
- **Validation:** [Pydantic](https://docs.pydantic.dev/)

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
