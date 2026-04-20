#!/usr/bin/env python3
"""Owner-wide GitHub portfolio scan for market and release readiness.

Uses GitHub API tree inspection (no local clone required), so it works even when
repositories contain Windows-incompatible filenames.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Dict, List, Optional

import requests

API_BASE = "https://api.github.com"


def gh_get(url: str, token: Optional[str], params: Optional[dict] = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_repos(owner: str, token: Optional[str], owner_type: str) -> List[dict]:
    repos: List[dict] = []
    page = 1
    while True:
        if owner_type == "org":
            url = f"{API_BASE}/orgs/{owner}/repos"
            params = {"per_page": 100, "page": page, "type": "public"}
        else:
            url = f"{API_BASE}/users/{owner}/repos"
            params = {"per_page": 100, "page": page}
        data = gh_get(url, token, params=params)
        if not data:
            break
        repos.extend([r for r in data if not r.get("archived", False)])
        page += 1
    return repos


def repo_paths(owner: str, repo: str, branch: str, token: Optional[str]) -> set[str]:
    branch_data = gh_get(f"{API_BASE}/repos/{owner}/{repo}/branches/{branch}", token)
    sha = branch_data["commit"]["sha"]
    tree = gh_get(f"{API_BASE}/repos/{owner}/{repo}/git/trees/{sha}", token, params={"recursive": 1})
    return {item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"}


def detect(paths: set[str]) -> Dict[str, bool]:
    return {
        "has_ci": any(p.startswith(".github/workflows/") for p in paths),
        "has_tests": any(p.startswith("tests/") for p in paths) or "pytest.ini" in paths or "package.json" in paths,
        "has_container": "Dockerfile" in paths or "docker-compose.yml" in paths or any("/Dockerfile" in p for p in paths),
        "has_security": "SECURITY.md" in paths,
        "has_license": "LICENSE" in paths or "LICENSE.md" in paths,
        "has_readme": "README.md" in paths,
        "has_mobile_signal": any(p.startswith("android/") for p in paths) or any(p.startswith("ios/") for p in paths) or "pubspec.yaml" in paths or "capacitor.config.ts" in paths or "capacitor.config.json" in paths,
        "has_observability": any("prometheus" in p.lower() or "grafana" in p.lower() or "otel" in p.lower() or "opentelemetry" in p.lower() for p in paths),
        "has_api_contract": "openapi.yaml" in paths or "openapi.yml" in paths or "swagger.yaml" in paths or "swagger.yml" in paths,
        "has_release_doc": "RELEASE.md" in paths or "docs/release.md" in paths,
    }


def score(signals: Dict[str, bool]) -> int:
    weights = {
        "has_ci": 15,
        "has_tests": 15,
        "has_container": 10,
        "has_security": 10,
        "has_license": 8,
        "has_readme": 8,
        "has_observability": 8,
        "has_api_contract": 8,
        "has_release_doc": 8,
        "has_mobile_signal": 10,
    }
    total = sum(weights[k] for k, v in signals.items() if v and k in weights)
    return min(total, 100)


def pivots(signals: Dict[str, bool]) -> List[str]:
    ideas: List[str] = []
    if not signals["has_ci"]:
        ideas.append("Implement gated CI/CD with quality, security, and release checks")
    if not signals["has_tests"]:
        ideas.append("Add unit/integration tests with coverage threshold enforcement")
    if not signals["has_security"]:
        ideas.append("Add SECURITY.md and enable vulnerability/secret scanning")
    if not signals["has_observability"]:
        ideas.append("Add OpenTelemetry traces, metrics, and SLO-based alerting")
    if not signals["has_api_contract"]:
        ideas.append("Publish and enforce OpenAPI contract compatibility checks")
    if not signals["has_release_doc"]:
        ideas.append("Create release checklist with rollback criteria and ownership")
    if not signals["has_mobile_signal"]:
        ideas.append("If mobile product: add app/play store release pipeline and crash analytics")
    ideas.append("Build growth moat with activation funnel and retention experimentation")
    return ideas[:8]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan GitHub owner repositories for market readiness")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--owner-type", choices=["user", "org"], default="user")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--report", default="portfolio_market_readiness.json")
    args = parser.parse_args()

    token = os.getenv(args.token_env)
    repos = list_repos(args.owner, token, args.owner_type)

    results = []
    for repo in repos:
        name = repo["name"]
        default_branch = repo.get("default_branch", "main")
        try:
            paths = repo_paths(args.owner, name, default_branch, token)
            signals = detect(paths)
            results.append(
                {
                    "repo": name,
                    "status": "scanned",
                    "score": score(signals),
                    "signals": signals,
                    "priority_pivots": pivots(signals),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "repo": name,
                    "status": "failed",
                    "score": 0,
                    "error": str(exc),
                    "priority_pivots": [
                        "Fix repository metadata/access and rerun portfolio scan",
                        "Add baseline CI/security/release files",
                    ],
                }
            )

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    report = {
        "owner": args.owner,
        "repo_count": len(results),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results,
    }

    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print(f"Saved {args.report}")
    print(f"Repos scanned: {len(results)}")
    print(f"Repos >= 70 score: {sum(1 for r in results if r.get('score', 0) >= 70)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
