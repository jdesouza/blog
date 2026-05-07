"""Minimal GitHub PR tool for CrewAI agents.

Uses the GitHub REST API directly (via httpx, already a CrewAI dep) so we
don't pull a third-party SaaS or extra package. One env var required at
runtime: GITHUB_TOKEN with contents:write + pull_requests:write on the
target repo. The token is read lazily inside _run so module import never
fails if the var is missing (matches what we did for GEMINI_API_KEY).
"""

from __future__ import annotations

import base64
import os
from typing import Type

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


_GITHUB_API = "https://api.github.com"
_TIMEOUT = 30.0


def _gh_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. Add it to the deployment environment "
            "(scopes: contents:write, pull_requests:write on the target repo)."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "crewai-blog-remediation-bot",
    }


class _ReadRepoFileArgs(BaseModel):
    repo_full_name: str = Field(
        ...,
        description='Repository in "owner/repo" form, e.g. "jdesouza/blog".',
    )
    file_path: str = Field(
        ..., description="Path to the file in the repo, e.g. 'failing.yaml'."
    )
    ref: str = Field(
        default="main",
        description="Branch, tag, or commit SHA to read from. Defaults to 'main'.",
    )


class ReadRepoFileTool(BaseTool):
    name: str = "read_repo_file"
    description: str = (
        "Read the current text contents of a file from a GitHub repository at "
        "a given ref (branch). Returns the file contents as a string. Use this "
        "before composing a fix so the patch is based on the real source."
    )
    args_schema: Type[BaseModel] = _ReadRepoFileArgs

    def _run(self, repo_full_name: str, file_path: str, ref: str = "main") -> str:
        url = f"{_GITHUB_API}/repos/{repo_full_name}/contents/{file_path}"
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(url, params={"ref": ref}, headers=_gh_headers())
        if r.status_code == 404:
            return f"ERROR: file '{file_path}' not found in {repo_full_name}@{ref}"
        r.raise_for_status()
        payload = r.json()
        if payload.get("encoding") != "base64" or "content" not in payload:
            return f"ERROR: unexpected response shape: keys={list(payload)}"
        decoded = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
        return decoded


class _OpenPullRequestArgs(BaseModel):
    repo_full_name: str = Field(
        ..., description='Repository in "owner/repo" form, e.g. "jdesouza/blog".'
    )
    base_branch: str = Field(
        default="main", description="Branch to merge the PR into. Defaults to 'main'."
    )
    head_branch: str = Field(
        ...,
        description=(
            "New branch name to create with the fix, e.g. "
            "'crewai/fix-priv-escalation'. Must not exist yet."
        ),
    )
    file_path: str = Field(
        ..., description="Path to the file being patched, e.g. 'failing.yaml'."
    )
    new_content: str = Field(
        ...,
        description=(
            "FULL new contents of the file after applying the fix. The tool "
            "writes this exact text. Do NOT pass a unified diff."
        ),
    )
    commit_message: str = Field(
        ...,
        description=(
            "One-line commit message, e.g. "
            "'fix(failing.yaml): set allowPrivilegeEscalation=false'."
        ),
    )
    pr_title: str = Field(..., description="Title of the pull request.")
    pr_body: str = Field(
        default="",
        description="Markdown body of the pull request. Include rationale and links.",
    )
    draft: bool = Field(
        default=True,
        description="Open the PR as draft. Defaults to True for safety.",
    )


class OpenPullRequestTool(BaseTool):
    name: str = "open_pull_request"
    description: str = (
        "Create a branch from base_branch, commit a single-file change with the "
        "given new_content, and open a pull request. Returns the PR URL on success. "
        "Use only AFTER you have read the current file with read_repo_file and "
        "computed the fully-fixed file contents."
    )
    args_schema: Type[BaseModel] = _OpenPullRequestArgs

    def _run(
        self,
        repo_full_name: str,
        head_branch: str,
        file_path: str,
        new_content: str,
        commit_message: str,
        pr_title: str,
        base_branch: str = "main",
        pr_body: str = "",
        draft: bool = True,
    ) -> str:
        headers = _gh_headers()
        with httpx.Client(timeout=_TIMEOUT, headers=headers) as client:
            base_ref = client.get(
                f"{_GITHUB_API}/repos/{repo_full_name}/git/ref/heads/{base_branch}"
            )
            if base_ref.status_code != 200:
                return (
                    f"ERROR: cannot read base branch '{base_branch}' on "
                    f"{repo_full_name}: HTTP {base_ref.status_code} "
                    f"{base_ref.text[:200]}"
                )
            base_sha = base_ref.json()["object"]["sha"]

            mk_branch = client.post(
                f"{_GITHUB_API}/repos/{repo_full_name}/git/refs",
                json={"ref": f"refs/heads/{head_branch}", "sha": base_sha},
            )
            if mk_branch.status_code not in (200, 201):
                if mk_branch.status_code == 422:
                    return (
                        f"ERROR: branch '{head_branch}' already exists on "
                        f"{repo_full_name}. Pick a unique name and retry."
                    )
                return (
                    f"ERROR: failed to create branch '{head_branch}': "
                    f"HTTP {mk_branch.status_code} {mk_branch.text[:200]}"
                )

            existing = client.get(
                f"{_GITHUB_API}/repos/{repo_full_name}/contents/{file_path}",
                params={"ref": head_branch},
            )
            file_sha: str | None = None
            if existing.status_code == 200:
                file_sha = existing.json().get("sha")
            elif existing.status_code != 404:
                return (
                    f"ERROR: failed to look up '{file_path}' on '{head_branch}': "
                    f"HTTP {existing.status_code} {existing.text[:200]}"
                )

            put_payload: dict[str, object] = {
                "message": commit_message,
                "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"),
                "branch": head_branch,
            }
            if file_sha:
                put_payload["sha"] = file_sha

            commit = client.put(
                f"{_GITHUB_API}/repos/{repo_full_name}/contents/{file_path}",
                json=put_payload,
            )
            if commit.status_code not in (200, 201):
                return (
                    f"ERROR: commit failed for '{file_path}': "
                    f"HTTP {commit.status_code} {commit.text[:200]}"
                )

            pr = client.post(
                f"{_GITHUB_API}/repos/{repo_full_name}/pulls",
                json={
                    "title": pr_title,
                    "head": head_branch,
                    "base": base_branch,
                    "body": pr_body,
                    "draft": draft,
                },
            )
            if pr.status_code not in (200, 201):
                return (
                    f"ERROR: pull request creation failed: "
                    f"HTTP {pr.status_code} {pr.text[:200]}"
                )

            data = pr.json()
            return (
                f"OK: opened {'draft ' if draft else ''}PR #{data['number']} "
                f"-> {data['html_url']}"
            )
