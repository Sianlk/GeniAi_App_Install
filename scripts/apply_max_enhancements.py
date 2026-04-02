#!/usr/bin/env python3
"""Apply maximum baseline enhancements across all repositories for an owner.

This script uses GitHub REST APIs directly with Python stdlib only.
It can run in dry-run mode without a token for public repositories, and in apply mode
with a token to create branches, commit improvements, and open PRs.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

API_BASE = "https://api.github.com"


def api_request(method: str, url: str, token: Optional[str], payload: Optional[dict] = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "max-enhancement-engine",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {body[:400]}") from exc


def list_repos(owner: str, owner_type: str, token: Optional[str], include_private: bool) -> List[dict]:
    repos: List[dict] = []
    page = 1
    while True:
        if owner_type == "org":
            repo_type = "all" if include_private else "public"
            url = f"{API_BASE}/orgs/{owner}/repos?per_page=100&page={page}&type={repo_type}"
        else:
            if include_private:
                url = (
                    f"{API_BASE}/user/repos?per_page=100&page={page}&visibility=all"
                    "&affiliation=owner,collaborator,organization_member"
                )
            else:
                url = f"{API_BASE}/users/{owner}/repos?per_page=100&page={page}"

        batch = api_request("GET", url, token)
        if not batch:
            break

        filtered = [r for r in batch if not r.get("archived", False)]
        if owner_type == "user" and include_private:
            filtered = [r for r in filtered if str((r.get("owner") or {}).get("login", "")).lower() == owner.lower()]

        repos.extend(filtered)
        page += 1

    return repos


def content_exists(owner: str, repo: str, path: str, branch: str, token: Optional[str]) -> bool:
    path_encoded = urllib.parse.quote(path, safe="/")
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path_encoded}?ref={urllib.parse.quote(branch)}"
    try:
        api_request("GET", url, token)
        return True
    except RuntimeError:
        return False


def build_templates() -> Dict[str, str]:
    return {
        ".github/workflows/release-quality.yml": """name: Release Quality Gate
on:
  pull_request:
  push:
    branches: [ main, master ]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Python quality gates
        run: |
          if [ -f requirements.txt ]; then python -m pip install -r requirements.txt; fi
          if [ -d tests ]; then python -m pip install pytest; python -m pytest -q || exit 1; fi
      - name: Node quality gates
        run: |
          if [ -f package.json ]; then npm install; npm test --if-present; npm run build --if-present; fi
""",
        ".github/workflows/security-scan.yml": """name: Security Scan
on:
  pull_request:
  push:
    branches: [ main, master ]

jobs:
  security:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Python dependency audit
        run: |
          if [ -f requirements.txt ] || [ -f pyproject.toml ]; then
            python -m pip install --upgrade pip pip-audit
            python -m pip_audit
          fi
      - name: Node dependency audit
        run: |
          if [ -f package.json ]; then npm install; npm audit --audit-level=high; fi
""",
        "SECURITY.md": """# Security Policy

## Supported Versions
Latest stable release is supported.

## Reporting a Vulnerability
Report security issues privately through repository security advisories or contact the maintainers directly.
""",
        "RELEASE.md": """# Release Checklist

- [ ] Tests pass in CI
- [ ] Security checks pass
- [ ] Version updated
- [ ] Changelog updated
- [ ] Rollback plan documented
- [ ] Incident response owner assigned
- [ ] App Store / Play Store metadata validated (if mobile)
""",
        "CONTRIBUTING.md": """# Contributing

## Engineering Bar
- Keep PRs small and focused.
- Add or update tests for behavior changes.
- CI and security gates must pass before merge.

## Review and Release
- At least one approval required.
- No unresolved high-severity vulnerabilities on release branches.
""",
        ".github/CODEOWNERS": """* @OWNER_USERNAME
""",
        "docs/OBSERVABILITY.md": """# Observability Baseline

- Structured logs with correlation IDs
- Latency, throughput, and error-rate metrics
- Error budget alerting
- Tracing for critical user journeys
""",
        "docs/GO_TO_MARKET.md": """# Go-To-Market Plan

## Product Moat
- Focus on one high-value problem and achieve 10x user outcome.
- Build proprietary feedback loops to improve model and product quality.

## Growth Loop
- Instrument activation funnel end-to-end.
- Build referral and lifecycle automation loops.

## Retention
- Cohort analysis each week.
- Rapid experiment pipeline for onboarding and habit loops.
""",
        "mobile/STORE_RELEASE_CHECKLIST.md": """# App and Play Store Checklist

- [ ] Signing and provisioning configured
- [ ] Privacy policy and support URLs configured
- [ ] Store metadata and screenshots updated
- [ ] Crash reporting and analytics validated
- [ ] Staged rollout and rollback criteria defined
""",
        "LICENSE": """MIT License

Copyright (c) 2026 OWNER

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    }


def create_branch(owner: str, repo: str, base_branch: str, branch: str, token: str) -> None:
    ref = api_request("GET", f"{API_BASE}/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(base_branch)}", token)
    sha = ref["object"]["sha"]
    api_request(
        "POST",
        f"{API_BASE}/repos/{owner}/{repo}/git/refs",
        token,
        {"ref": f"refs/heads/{branch}", "sha": sha},
    )


def put_file(owner: str, repo: str, branch: str, path: str, content: str, token: str) -> None:
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    path_encoded = urllib.parse.quote(path, safe="/")
    api_request(
        "PUT",
        f"{API_BASE}/repos/{owner}/{repo}/contents/{path_encoded}",
        token,
        {
            "message": f"chore: add enhancement baseline {path}",
            "content": content_b64,
            "branch": branch,
        },
    )


def create_pr(owner: str, repo: str, branch: str, base_branch: str, token: str) -> str:
    data = api_request(
        "POST",
        f"{API_BASE}/repos/{owner}/{repo}/pulls",
        token,
        {
            "title": "chore: max enhancement baseline for quality, security, and growth",
            "head": branch,
            "base": base_branch,
            "body": (
                "Automated enhancement baseline PR.\n\n"
                "Includes CI quality gates, security scans, release controls, observability, "
                "store-release checklist, and go-to-market planning artifacts."
            ),
        },
    )
    return str(data.get("html_url", ""))


def plan_repo(owner: str, repo: str, branch: str, token: Optional[str], templates: Dict[str, str]) -> List[str]:
    needed: List[str] = []
    for path in templates:
        if not content_exists(owner, repo, path, branch, token):
            needed.append(path)
    return needed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply max enhancements to all owner repositories")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--owner-type", choices=["user", "org"], default="user")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--include-private", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Apply changes and open PRs")
    parser.add_argument("--branch", default="chore/max-enhancement-baseline")
    parser.add_argument("--report", default="max_enhancement_report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv(args.token_env)

    if args.apply and not token:
        print(f"Error: apply mode requires token in {args.token_env}")
        return 2
    if args.include_private and not token:
        print(f"Error: include-private requires token in {args.token_env}")
        return 2

    templates = build_templates()
    repos = list_repos(args.owner, args.owner_type, token, include_private=args.include_private)

    report: Dict[str, object] = {
        "owner": args.owner,
        "owner_type": args.owner_type,
        "include_private": args.include_private,
        "apply": args.apply,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo_count": len(repos),
        "repos": [],
    }

    for repo_data in repos:
        repo = str(repo_data["name"])
        default_branch = str(repo_data.get("default_branch", "main"))
        missing = plan_repo(args.owner, repo, default_branch, token, templates)
        item = {
            "repo": repo,
            "default_branch": default_branch,
            "missing_enhancements": missing,
            "applied": False,
            "pr_url": "",
            "error": "",
        }

        if args.apply and missing:
            try:
                try:
                    create_branch(args.owner, repo, default_branch, args.branch, token or "")
                except Exception:
                    pass

                for path in missing:
                    put_file(args.owner, repo, args.branch, path, templates[path], token or "")
                item["pr_url"] = create_pr(args.owner, repo, args.branch, default_branch, token or "")
                item["applied"] = True
            except Exception as exc:
                item["error"] = str(exc)

        report["repos"].append(item)

    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    planned = sum(1 for r in report["repos"] if r["missing_enhancements"])
    applied = sum(1 for r in report["repos"] if r["applied"])
    print(f"Saved {args.report}")
    print(f"Repositories analyzed: {report['repo_count']}")
    print(f"Repositories with enhancements planned: {planned}")
    if args.apply:
        print(f"Enhancement PRs created: {applied}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
