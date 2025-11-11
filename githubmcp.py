from typing import Optional, List
import os
import requests
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

GITHUB_API_BASE = "https://api.github.com"

app = FastAPI(title="FastAPI GitHub MCP Server", version="0.1.0")

# Allow localhost from VS Code / other tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Utilities --------------------

def get_token(authorization: Optional[str] = Header(None)) -> str:
    """Resolve GitHub token from Authorization header (Bearer ...) or env var GITHUB_TOKEN"""
    if authorization:
        # allow "Bearer TOKEN" or direct token
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return authorization
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise HTTPException(status_code=401, detail="GitHub token not provided via Authorization header or GITHUB_TOKEN env var")
    return token


def gh_request(method: str, path: str, token: str, json: Optional[dict] = None, params: Optional[dict] = None):
    print(token)
    url = f"{GITHUB_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.request(method, url, headers=headers, json=json, params=params)
    if resp.status_code >= 400:
        # bubble up GitHub error message
        try:
            detail = resp.json()
        except Exception:
            detail = {"message": resp.text}
        raise HTTPException(status_code=resp.status_code, detail=detail)
    try:
        return resp.json()
    except ValueError:
        return {"status": "ok"}

# -------------------- Pydantic models --------------------

class CreateBranchPayload(BaseModel):
    new_branch: str
    base_branch: Optional[str] = "main"

class CreatePrPayload(BaseModel):
    head: str  # branch name (owner:branch or branch)
    base: str = "main"
    title: str
    body: Optional[str] = None
    draft: Optional[bool] = False

class ReviewPrPayload(BaseModel):
    body: Optional[str] = None
    event: Optional[str] = "COMMENT"  # COMMENT, APPROVE, REQUEST_CHANGES

class MergePrPayload(BaseModel):
    commit_title: Optional[str] = None
    commit_message: Optional[str] = None
    merge_method: Optional[str] = "merge"  # merge, squash, rebase

# -------------------- MCP & Health --------------------

MCP_MANIFEST = {
    "name": "local-github-mcp",
    "version": "0.1.0",
    "description": "Local GitHub MCP providing repo operations for Copilot / VS Code",
    "modes": ["completion", "chat"],
    "schemaVersion": "1.0.0",
}


@app.get("/mcp")
def mcp_manifest():
    """Return a small manifest for MCP registration (VS Code expects a JSON manifest)."""
    return MCP_MANIFEST


@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------- Branch endpoints --------------------

@app.get("/repos/{owner}/{repo}/branches")
def list_branches(owner: str, repo: str, token: str = Depends(get_token)):
    """List branches for a repo"""
    path = f"/repos/{owner}/{repo}/branches"
    return gh_request("GET", path, token)


@app.post("/repos/{owner}/{repo}/branches")
def create_branch(owner: str, repo: str, payload: CreateBranchPayload, token: str = Depends(get_token)):
    """Create a new branch by creating a new ref from base branch's commit SHA"""
    # 1) get base branch sha
    base_path = f"/repos/{owner}/{repo}/git/ref/heads/{payload.base_branch}"
    base_ref = gh_request("GET", base_path, token)
    base_sha = base_ref.get("object", {}).get("sha")
    if not base_sha:
        raise HTTPException(status_code=500, detail="Could not resolve base branch SHA")
    # 2) create new ref
    ref_path = f"/repos/{owner}/{repo}/git/refs"
    new_ref = {"ref": f"refs/heads/{payload.new_branch}", "sha": base_sha}
    return gh_request("POST", ref_path, token, json=new_ref)

# -------------------- PR endpoints --------------------

@app.get("/repos/{owner}/{repo}/prs")
def list_prs(owner: str, repo: str, state: str = "open", token: str = Depends(get_token)):
    path = f"/repos/{owner}/{repo}/pulls"
    return gh_request("GET", path, token, params={"state": state})


@app.post("/repos/{owner}/{repo}/prs")
def create_pr(owner: str, repo: str, payload: CreatePrPayload, token: str = Depends(get_token)):
    path = f"/repos/{owner}/{repo}/pulls"
    body = {"title": payload.title, "head": payload.head, "base": payload.base, "body": payload.body, "draft": payload.draft}
    return gh_request("POST", path, token, json=body)


@app.get("/repos/{owner}/{repo}/prs/{pr_number}")
def get_pr(owner: str, repo: str, pr_number: int, token: str = Depends(get_token)):
    path = f"/repos/{owner}/{repo}/pulls/{pr_number}"
    return gh_request("GET", path, token)


@app.post("/repos/{owner}/{repo}/prs/{pr_number}/reviews")
def review_pr(owner: str, repo: str, pr_number: int, payload: ReviewPrPayload, token: str = Depends(get_token)):
    path = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    body = {"body": payload.body or "", "event": payload.event}
    return gh_request("POST", path, token, json=body)


@app.post("/repos/{owner}/{repo}/prs/{pr_number}/merge")
def merge_pr(owner: str, repo: str, pr_number: int, payload: MergePrPayload, token: str = Depends(get_token)):
    path = f"/repos/{owner}/{repo}/pulls/{pr_number}/merge"
    body = {"commit_title": payload.commit_title, "commit_message": payload.commit_message, "merge_method": payload.merge_method}
    return gh_request("PUT", path, token, json=body)

# -------------------- Additional helpers --------------------

@app.get("/repos/{owner}/{repo}/contents/{path:path}")
def get_contents(owner: str, repo: str, path: str, ref: Optional[str] = None, token: str = Depends(get_token)):
    """Get repository file contents (useful for previews)
    URL: /repos/{owner}/{repo}/contents/{path}?ref=branch
    """
    api_path = f"/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": ref} if ref else None
    return gh_request("GET", api_path, token, params=params)

# -------------------- Root landing page --------------------

@app.get("/")
async def root(request: Request):
    base = str(request.base_url)
    return {
        "message": "FastAPI GitHub MCP Server",
        "mcp_manifest": f"{base}mcp",
        "health": f"{base}health",
    }

# -------------------- Run locally --------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("githubmcp:app", host="0.0.0.0", port=8000, reload=True)
