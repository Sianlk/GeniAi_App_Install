#!/usr/bin/env python3
"""Create standards PRs across GitHub repositories.

This script uses GitHub APIs to add missing baseline files and workflows so repos are
closer to production and store-release readiness.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

API_BASE = "https://api.github.com"


@dataclass
class ChangePlan:
    repo: str
    default_branch: str
    branch: str
    files_to_add: Dict[str, str]


def headers(token: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def gh_get(url: str, token: str) -> dict:
    resp = requests.get(url, headers=headers(token), timeout=30)
    resp.raise_for_status()
    return resp.json()


def gh_post(url: str, token: str, payload: dict) -> dict:
    resp = requests.post(url, headers=headers(token), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def gh_put(url: str, token: str, payload: dict) -> dict:
    resp = requests.put(url, headers=headers(token), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_repos(owner: str, token: str, owner_type: str, include_private: bool) -> List[dict]:
    repos = []
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
        data = gh_get(url, token)
        if not data:
            break
        filtered = [r for r in data if not r.get("archived", False)]
        if owner_type == "user" and include_private:
            filtered = [r for r in filtered if str(r.get("owner", {}).get("login", "")).lower() == owner.lower()]
        repos.extend(filtered)
        page += 1
    return repos


def file_exists(owner: str, repo: str, path: str, ref: str, token: str) -> bool:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    resp = requests.get(url, headers=headers(token), timeout=30)
    return resp.status_code == 200


def default_templates(repo_name: str) -> Dict[str, str]:
    return {
        ".github/workflows/release-quality.yml": """name: Release Quality Gate\non:\n  pull_request:\n  push:\n    branches: [ main, master ]\n\njobs:\n  quality:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Setup Node\n        uses: actions/setup-node@v4\n        with:\n          node-version: '20'\n      - name: Setup Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - name: Install Python deps (if present)\n        run: |\n          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi\n      - name: Python tests (if present)\n        run: |\n          if [ -d tests ]; then python -m pytest -q || exit 1; fi\n      - name: Node install/test (if present)\n        run: |\n          if [ -f package.json ]; then npm install; npm test --if-present; npm run build --if-present; fi\n""",
        ".github/workflows/security-scan.yml": """name: Security Scan\non:\n  pull_request:\n  push:\n    branches: [ main, master ]\n\njobs:\n  security:\n    runs-on: ubuntu-latest\n    permissions:\n      contents: read\n      security-events: write\n    steps:\n      - uses: actions/checkout@v4\n      - name: Setup Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - name: Python dependency audit\n        run: |\n          if [ -f requirements.txt ] || [ -f pyproject.toml ]; then\n            python -m pip install --upgrade pip pip-audit\n            python -m pip_audit\n          fi\n      - name: Node dependency audit\n        run: |\n          if [ -f package.json ]; then npm install; npm audit --audit-level=high; fi\n""",
        ".github/CODEOWNERS": """* @OWNER_USERNAME\n""",
        "CONTRIBUTING.md": """# Contributing\n\n## Development Standards\n- Keep pull requests focused and small.\n- Add tests for behavior changes.\n- Ensure CI, security scan, and release checks pass before merge.\n\n## Review Requirements\n- At least one reviewer approval.\n- No unresolved security findings for release branches.\n""",
        "SECURITY.md": """# Security Policy\n\n## Supported Versions\nLatest stable release is supported.\n\n## Reporting a Vulnerability\nReport security issues privately through repository security advisories or contact the maintainers directly.\n""",
        "RELEASE.md": """# Release Checklist\n\n- [ ] Tests pass in CI\n- [ ] Security checks pass\n- [ ] Version updated\n- [ ] Changelog updated\n- [ ] Rollback plan documented\n- [ ] App Store / Play Store metadata validated (if mobile)\n""",
        "docs/OBSERVABILITY.md": """# Observability Baseline\n\n## Minimum Requirements\n- Structured logs with request correlation IDs\n- Service-level latency and error metrics\n- Alerting on error budget burn\n- Dashboard for deployment and release impact\n\n## Recommended Stack\n- OpenTelemetry for traces and metrics\n- Prometheus/Grafana (or managed equivalents)\n""",
        "docs/GO_TO_MARKET.md": """# Go-To-Market Playbook\n\n## Product Moat\n- Identify one defensible user problem where this product is 10x better.\n- Build proprietary data feedback loops that improve outcomes over time.\n\n## Growth Loop\n- Activation funnel instrumentation from first visit to successful outcome.\n- Referral and partnership channels with measurable CAC and payback.\n\n## Retention\n- Lifecycle messaging and re-engagement experiments.\n- Weekly cohort review of retention and churn drivers.\n""",
        "mobile/STORE_RELEASE_CHECKLIST.md": """# App Store / Play Store Release Checklist\n\n- [ ] Bundle ID / Application ID validated\n- [ ] Code signing and keystore provisioning confirmed\n- [ ] Privacy policy URL and support URL configured\n- [ ] Store screenshots and metadata updated\n- [ ] Crash reporting and analytics enabled\n- [ ] Rollout strategy and rollback criteria defined\n""",
        "LICENSE": """MIT License\n\nCopyright (c) 2026 {repo}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n""".format(repo=repo_name),
    }


def create_branch(owner: str, repo: str, base_branch: str, new_branch: str, token: str) -> None:
    base = gh_get(f"{API_BASE}/repos/{owner}/{repo}/git/ref/heads/{base_branch}", token)
    sha = base["object"]["sha"]
    gh_post(
        f"{API_BASE}/repos/{owner}/{repo}/git/refs",
        token,
        {"ref": f"refs/heads/{new_branch}", "sha": sha},
    )


def put_file(owner: str, repo: str, branch: str, path: str, content: str, token: str) -> None:
    payload = {
        "message": f"chore: add baseline standard {path}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    gh_put(f"{API_BASE}/repos/{owner}/{repo}/contents/{path}", token, payload)


def create_pr(owner: str, repo: str, branch: str, base_branch: str, token: str) -> str:
    body = (
        "Automated standards PR to improve production readiness and release quality.\n\n"
        "Includes CI workflow, security policy, release checklist, and license baseline where missing."
    )
    data = gh_post(
        f"{API_BASE}/repos/{owner}/{repo}/pulls",
        token,
        {
            "title": "chore: baseline standards for production readiness",
            "head": branch,
            "base": base_branch,
            "body": body,
        },
    )
    return data.get("html_url", "")


def build_plan(owner: str, repo: str, default_branch: str, token: str) -> ChangePlan:
    templates = default_templates(repo)
    files_to_add = {}
    for path, content in templates.items():
        if not file_exists(owner, repo, path, default_branch, token):
            files_to_add[path] = content

    return ChangePlan(
        repo=repo,
        default_branch=default_branch,
        branch="chore/production-standards-baseline",
        files_to_add=files_to_add,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standardize GitHub repositories for production readiness")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--owner-type", choices=["user", "org"], default="user")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--include-private", action="store_true", help="Include private repositories")
    parser.add_argument("--apply", action="store_true", help="Apply changes and create PRs")
    parser.add_argument("--report", default="repo_standardization_report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv(args.token_env)
    if not token:
        print(f"Missing token env var: {args.token_env}")
        return 2

    repos = list_repos(args.owner, token, args.owner_type, include_private=args.include_private)
    report = {
        "owner": args.owner,
        "include_private": args.include_private,
        "repo_count": len(repos),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repositories": [],
    }

    for repo_data in repos:
        repo = repo_data["name"]
        default_branch = repo_data.get("default_branch", "main")
        plan = build_plan(args.owner, repo, default_branch, token)

        item = {
            "repo": repo,
            "default_branch": default_branch,
            "planned_files": sorted(plan.files_to_add.keys()),
            "applied": False,
            "pr_url": "",
            "error": "",
        }

        if args.apply and plan.files_to_add:
            try:
                create_branch(args.owner, repo, default_branch, plan.branch, token)
                for path, content in plan.files_to_add.items():
                    put_file(args.owner, repo, plan.branch, path, content, token)
                item["pr_url"] = create_pr(args.owner, repo, plan.branch, default_branch, token)
                item["applied"] = True
            except Exception as exc:
                item["error"] = str(exc)

        report["repositories"].append(item)

    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print(f"Saved {args.report}")
    print(f"Repositories analyzed: {report['repo_count']}")
    print(f"Repositories with changes planned: {sum(1 for r in report['repositories'] if r['planned_files'])}")
    if args.apply:
        print(f"PRs created: {sum(1 for r in report['repositories'] if r['pr_url'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
