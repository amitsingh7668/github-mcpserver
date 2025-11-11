# 🧩 FastAPI GitHub MCP Server

A lightweight **FastAPI-based MCP (Model Context Protocol) server** that exposes GitHub repository operations to **VS Code Copilot** or any MCP-compatible client.

This server allows you to:
- 🔍 List all branches in a repo
- 🌿 Create new branches
- 🔀 Open new Pull Requests (PRs)
- 🧾 View and review existing PRs
- ✅ Merge PRs
- 📂 View repository file contents

All via a local REST API that you can register as an **MCP endpoint** inside VS Code.

---

## 🚀 Features

| Operation | Endpoint | Method |
|------------|-----------|--------|
| Health Check | `/health` | GET |
| MCP Manifest | `/mcp` | GET |
| List branches | `/repos/{owner}/{repo}/branches` | GET |
| Create branch | `/repos/{owner}/{repo}/branches` | POST |
| List PRs | `/repos/{owner}/{repo}/prs` | GET |
| Open PR | `/repos/{owner}/{repo}/prs` | POST |
| Get PR | `/repos/{owner}/{repo}/prs/{pr_number}` | GET |
| Review PR | `/repos/{owner}/{repo}/prs/{pr_number}/reviews` | POST |
| Merge PR | `/repos/{owner}/{repo}/prs/{pr_number}/merge` | POST |

---

## ⚙️ Installation

### 1️⃣ Clone or copy this file
```bash
git clone <your-repo-url>
cd fastapi-github-mcp-server
```

### 2️⃣ Install dependencies
```bash
pip install fastapi uvicorn pydantic requests python-multipart
```

(Optional but recommended if using `.env`):
```bash
pip install python-dotenv
```

---

## 🔐 Authentication

The app requires a **GitHub Personal Access Token (PAT)**.

### Option A — via Environment Variable
```bash
export GITHUB_TOKEN=ghp_yourtokenhere   # macOS / Linux
set GITHUB_TOKEN=ghp_yourtokenhere      # Windows CMD
$env:GITHUB_TOKEN="ghp_yourtokenhere"   # PowerShell
```

### Option B — set from code (for local debugging)
```python
os.environ["GITHUB_TOKEN"] = "ghp_yourtokenhere"
```

### Option C — use `.env` file
Create a `.env` file in the root directory:
```
GITHUB_TOKEN=ghp_yourtokenhere
```
Then add this to the top of your Python file:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## ▶️ Running the Server

### Debug / Auto-reload Mode
```bash
uvicorn fastapi_github_mcp_server:app --reload --port 8000 --host 0.0.0.0
```

### With verbose logging
```bash
uvicorn fastapi_github_mcp_server:app --reload --log-level debug
```

### Or run directly
```bash
python fastapi_github_mcp_server.py
```

---

## 🧭 MCP Registration (VS Code Copilot)

Create a `.vscode/mcp.json` file in your workspace:

```json
{
  "name": "local-github-mcp",
  "version": "0.1.0",
  "description": "Local GitHub MCP providing repo operations",
  "modes": ["chat", "completion"],
  "schemaVersion": "1.0.0",
  "url": "http://localhost:8000/mcp"
}
```

Restart VS Code — Copilot will detect and register the MCP.

Now you can use prompts like:
> "List all open pull requests in repo `octocat/Hello-World`"
> "Create a new branch `feature/test` from `main`"
> "Open a PR from `feature/test` to `main`"

---

## 🧪 Example cURL Commands

### List branches
```bash
curl -H "Authorization: Bearer ghp_yourtoken" \
  http://localhost:8000/repos/octocat/Hello-World/branches
```

### Create a branch
```bash
curl -X POST -H "Authorization: Bearer ghp_yourtoken" \
  -H "Content-Type: application/json" \
  -d '{"new_branch": "feature/test", "base_branch": "main"}' \
  http://localhost:8000/repos/octocat/Hello-World/branches
```

### Open a PR
```bash
curl -X POST -H "Authorization: Bearer ghp_yourtoken" \
  -H "Content-Type: application/json" \
  -d '{"title": "Add feature", "head": "feature/test", "base": "main"}' \
  http://localhost:8000/repos/octocat/Hello-World/prs
```

### Review a PR
```bash
curl -X POST -H "Authorization: Bearer ghp_yourtoken" \
  -H "Content-Type: application/json" \
  -d '{"body": "Looks good!", "event": "APPROVE"}' \
  http://localhost:8000/repos/octocat/Hello-World/prs/123/reviews
```

### Merge a PR
```bash
curl -X POST -H "Authorization: Bearer ghp_yourtoken" \
  -H "Content-Type: application/json" \
  -d '{"commit_title": "Merging PR 123", "merge_method": "squash"}' \
  http://localhost:8000/repos/octocat/Hello-World/prs/123/merge
```

---

## 🧰 VS Code Debug Configuration

In `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI MCP Server",
      "type": "python",
      "request": "launch",
      "program": "uvicorn",
      "args": [
        "fastapi_github_mcp_server:app",
        "--reload",
        "--port", "8000",
        "--log-level", "debug"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_yourtokenhere"
      }
    }
  ]
}
```

Then press **F5** to run and debug.

---

## 🧩 Notes
- Make sure your GitHub token has the `repo` scope.
- Don’t commit your token or `.env` file to public repos.
- For production use, integrate a secure secrets manager (e.g., AWS Secrets Manager, Azure Key Vault).

---

## 🧑‍💻 Author
**Amit Singh**  
FastAPI + GitHub MCP Automation Demo — 2025
