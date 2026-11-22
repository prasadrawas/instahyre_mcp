# Instahyre MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Specification](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Official%20SDK-orange.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready **Model Context Protocol (MCP)** server for **[Instahyre](https://www.instahyre.com)** (India's premier AI-driven tech hiring and talent discovery platform). Enables AI assistants (Claude Web, Claude Desktop, Gemini, ChatGPT, Cursor, and custom agentic workflows) to inspect candidate profiles, update skills and salary preferences, search matching opportunities, parse detailed job descriptions, manage the application pipeline, communicate with recruiters, and control employer privacy.

---

## 🌟 Key Capabilities

- **Zero-Config Multi-Tenant Remote Deployment**: Securely connects to **Claude Web** (Custom Connectors) and **Gemini** without needing environment variables on the server. Simply pass your credentials directly in the connection URL (`?sessionid=...&csrftoken=...&cf_clearance=...`).
- **Complete Profile & Career Management**: Fetch full candidate profiles, update current company/designation, experience, salary preferences, location preferences, and skills.
- **Automated Recruiter Activity Pulse (`touch_profile_pulse`)**: Simulates candidate activity timestamps ("Active Today"), ranking candidate profiles higher in recruiter search results.
- **Curated Tech Matching Feed & Job Search**:
  - `search_jobs` (without query): Automatically returns personalized curated matching opportunities tailored to your tech stack and experience.
  - `search_jobs` (with query): Parametric keyword search across 40,000+ live jobs in India.
  - `get_job_details`: Structured Schema.org `JobPosting` extraction, tech tags, company background, and hiring team insights.
- **Application Pipeline**:
  - `apply` / `pass`: Express interest in or decline opportunities.
  - `apply_bulk`: Submit applications to multiple matching jobs in one operation.
  - `list_applied` / `list_declined`: Track applied opportunities and historical pipeline.
  - `metrics`: Live breakdown of matching counts, top locations, and job functions.
- **Resume Extraction**: Parse and extract candidate resume text via PDF parsing (`pypdf`).
- **Employer Privacy & Settings**: Block competitor companies (`block_company` / `unblock_company`) from viewing your profile and manage notification channels.

---

## 🛠️ Unified 6-Tool Architecture

The Instahyre MCP server has been engineered into a high-performance **6-Tool Architecture**, reducing context token consumption by **~80%** while eliminating prompt pollution.

| Tool | Action Options / Capabilities | Description |
| :--- | :--- | :--- |
| **`manage_profile`** | `action`: `"get"`, `"update"`, `"pulse"`, `"get_resume"`, `"upload_resume"` | Complete candidate profile lifecycle: view profile, update career details/skills/salary preferences, bump recruiter search visibility pulse, and manage resumes. |
| **`search_jobs`** | `query`, `location`, `job_functions`, `limit`, `offset` | Discover tech openings. If query is omitted, automatically returns your personalized **Matching Opportunities Feed**. Otherwise, executes full parametric search. |
| **`get_job_details`** | `job_ids`: `Union[int, List[int]]`, `opportunity_url`: `str` | Comprehensive inspection for single or multiple jobs. Returns full JD, skills tags, employer background, and structured Schema.org JobPosting data. |
| **`manage_job_pipeline`** | `action`: `"apply"`, `"pass"`, `"apply_bulk"`, `"list_applied"`, `"list_declined"`, `"metrics"` | Complete application pipeline: express interest (apply), decline/pass, batch apply, inspect applied/declined opportunities, and fetch pipeline metrics. |
| **`manage_account`** | `action`: `"get_settings"`, `"update_settings"`, `"block_company"`, `"unblock_company"`, `"get_messages"`, `"suggest"` | Account settings, employer privacy (blocking competitor companies from seeing your profile), recruiter message inbox, and taxonomy autocomplete. |
| **`manage_session`** | `action`: `"validate"`, `"inspect"` | Candidate authentication verification and credential inspection. |

---

## 🚀 Quick Start & Connection Guide

### How to Retrieve Your Instahyre Credentials

1. Log in to your account on **[instahyre.com](https://www.instahyre.com)**.
2. Press `F12` (or `Cmd + Option + I` on macOS) to open Developer Tools.
3. Navigate to **Storage** (Firefox) or **Application** (Chrome) &rarr; **Cookies** &rarr; `https://www.instahyre.com`.
4. Copy the values for:
   - `sessionid` (Django session cookie)
   - `csrftoken` (Django CSRF token)
   - `cf_clearance` (Cloudflare clearance cookie)
5. In the **Console** tab, run `navigator.userAgent` to get your browser User-Agent.

---

### Connecting to Claude Web / Gemini Custom Connectors

In Claude Web or Gemini MCP connector setup, enter the HTTPS URL of your deployed server with your credentials appended:

```text
https://your-instahyre-mcp.up.railway.app/sse?sessionid=YOUR_SESSIONID&csrftoken=YOUR_CSRFTOKEN&cf_clearance=YOUR_CF_CLEARANCE
```

#### Supported URL Query Parameters:
- `?sessionid=<id>`: (Required) Your Instahyre session cookie.
- `&csrftoken=<token>`: (Required) Your Django CSRF token.
- `&cf_clearance=<token>`: (Required) Your Cloudflare clearance token.
- `&user_agent=<ua>`: (Optional) Your browser User-Agent matching `cf_clearance`.

*(The server natively supports both **Streamable HTTP** `/mcp` and **Server-Sent Events** `/sse`, with dual-transport method routing to prevent HTTP 405 errors).*

---

### Connecting to Claude Desktop / Cursor

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "instahyre": {
      "command": "python",
      "args": ["-m", "instahyre_mcp", "--transport", "stdio"],
      "env": {
        "INSTAHYRE_SESSIONID": "YOUR_SESSIONID",
        "INSTAHYRE_CSRFTOKEN": "YOUR_CSRFTOKEN",
        "INSTAHYRE_CF_CLEARANCE": "YOUR_CF_CLEARANCE",
        "INSTAHYRE_USER_AGENT": "YOUR_BROWSER_USER_AGENT"
      }
    }
  }
}
```

---

## 🐳 Docker & Cloud Deployment

### Run with Docker

```bash
docker build -t instahyre-mcp .
docker run -p 8000:8000 -e PORT=8000 instahyre-mcp
```

### 1-Click Cloud Deployment (Railway / Render / Fly.io)

1. Push this repository to GitHub.
2. Link the repository to Railway or Render.
3. Start command is automatically inferred from `Dockerfile`:
   ```bash
   python -m instahyre_mcp --transport sse --port ${PORT:-8000} --host 0.0.0.0
   ```
4. Access health probe at `https://<your-app>.up.railway.app/health`.

---

## 🧪 Running Automated Tests

```bash
# Run unit test suite
python -m unittest discover instahyre_mcp/tests

# Run live matrix suite against authentic endpoints
python -m unittest instahyre_mcp/tests/test_instahyre_live_matrix.py
```

---

## 📄 License

MIT License. Designed and crafted for AI-assisted tech career growth.
