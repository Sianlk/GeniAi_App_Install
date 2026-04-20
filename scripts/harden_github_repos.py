#!/usr/bin/env python3
"""Audit and harden multiple GitHub repositories with production-readiness gates.

Usage examples:
  python scripts/harden_github_repos.py --owner my-org --token-env GITHUB_TOKEN
  python scripts/harden_github_repos.py --owner my-org --repo repo-a --repo repo-b --fix --push
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

API_BASE = "https://api.github.com"
DEFAULT_TIMEOUT = 1200
DEFAULT_RETRIES = 3


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class RepoReport:
    repo: str
    path: str
    cloned: bool
    checks: Dict[str, str]
    commands: List[CommandResult]
    success: bool
    notes: List[str]
    pr_url: Optional[str] = None
    mobile_readiness_score: int = 0
    market_leadership_score: int = 0


def locate_git() -> str:
    git_path = shutil.which("git")
    if git_path:
        return git_path

    candidates = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    raise FileNotFoundError(
        "Git executable not found. Install Git and ensure it is in PATH."
    )


def run_cmd(cmd: List[str], cwd: Path, timeout: int = DEFAULT_TIMEOUT) -> CommandResult:
    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    ended = time.time()
    return CommandResult(
        command=" ".join(cmd),
        returncode=proc.returncode,
        stdout=proc.stdout[-12000:],
        stderr=proc.stderr[-12000:],
        duration_seconds=round(ended - started, 2),
    )


def _github_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request_with_retry(method: str, url: str, token: Optional[str], **kwargs: Any) -> requests.Response:
    last_error: Optional[Exception] = None
    for attempt in range(1, DEFAULT_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=_github_headers(token),
                timeout=30,
                **kwargs,
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < DEFAULT_RETRIES:
                sleep_s = min(8, 2 ** attempt) + random.random()
                time.sleep(sleep_s)
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == DEFAULT_RETRIES:
                break
            sleep_s = min(8, 2 ** attempt) + random.random()
            time.sleep(sleep_s)

    raise RuntimeError(f"GitHub API request failed after retries: {url}; error={last_error}")


def github_get(url: str, token: Optional[str], params: Optional[dict] = None) -> requests.Response:
    return _request_with_retry("GET", url, token, params=params)


def github_post(url: str, token: Optional[str], payload: dict) -> requests.Response:
    return _request_with_retry("POST", url, token, json=payload)


def detect_owner_type(owner: str, token: Optional[str]) -> str:
    url = f"{API_BASE}/users/{owner}"
    resp = github_get(url, token)
    owner_type = str(resp.json().get("type", "")).lower()
    return "org" if owner_type == "organization" else "user"


def get_authenticated_login(token: str) -> str:
    resp = github_get(f"{API_BASE}/user", token)
    return str(resp.json().get("login", ""))


def list_repos(owner: str, token: Optional[str], owner_type: str = "auto", include_private: bool = False) -> List[str]:
    resolved_owner_type = owner_type.lower()
    if resolved_owner_type == "auto":
        resolved_owner_type = detect_owner_type(owner, token)

    if resolved_owner_type not in {"user", "org"}:
        raise ValueError("owner_type must be one of: auto, user, org")

    if include_private and not token:
        raise ValueError("--include-private requires an authenticated token")

    repos: List[str] = []
    page = 1
    while True:
        if resolved_owner_type == "org":
            url = f"{API_BASE}/orgs/{owner}/repos"
            params = {"per_page": 100, "page": page, "type": "all" if include_private else "public"}
        else:
            if include_private:
                url = f"{API_BASE}/user/repos"
                params = {
                    "per_page": 100,
                    "page": page,
                    "visibility": "all",
                    "affiliation": "owner,collaborator,organization_member",
                }
            else:
                url = f"{API_BASE}/users/{owner}/repos"
                params = {"per_page": 100, "page": page}

        resp = github_get(url, token, params=params)
        data = resp.json()
        if not data:
            break

        filtered = [r for r in data if not r.get("archived", False)]
        if resolved_owner_type == "user" and include_private:
            filtered = [r for r in filtered if str(r.get("owner", {}).get("login", "")).lower() == owner.lower()]

        repos.extend([r["name"] for r in filtered])
        page += 1
    return sorted(set(repos))


def load_policy(policy_path: Path) -> Dict[str, Any]:
    if not policy_path.exists():
        return {
            "required_checks": ["ci_workflow"],
            "security_checks": ["python_deps", "node_deps"],
            "pr": {
                "create": False,
                "base": "main",
                "title_prefix": "chore: production hardening for",
            },
            "market_leadership": {
                "minimum_score": 70,
                "require_mobile_release_readiness": True,
            },
        }

    return json.loads(policy_path.read_text(encoding="utf-8"))


def detect_checks(repo_path: Path) -> Dict[str, str]:
    checks: Dict[str, str] = {
        "python": "skip",
        "node": "skip",
        "docker": "skip",
        "ci_workflow": "fail",
        "python_deps": "skip",
        "node_deps": "skip",
    }

    if (repo_path / ".github" / "workflows").exists():
        checks["ci_workflow"] = "pass"

    if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
        checks["python"] = "pending"

    if (repo_path / "package.json").exists():
        checks["node"] = "pending"

    if (repo_path / "Dockerfile").exists() or (repo_path / "docker-compose.yml").exists():
        checks["docker"] = "pending"

    return checks


def run_python_checks(repo_path: Path) -> List[CommandResult]:
    commands: List[CommandResult] = []
    python = shutil.which("python") or shutil.which("py")
    if not python:
        commands.append(
            CommandResult(
                command="python",
                returncode=1,
                stdout="",
                stderr="Python not found in PATH",
                duration_seconds=0,
            )
        )
        return commands

    if (repo_path / "requirements.txt").exists():
        commands.append(run_cmd([python, "-m", "pip", "install", "-r", "requirements.txt"], repo_path))

    if (repo_path / "pytest.ini").exists() or (repo_path / "tests").exists():
        commands.append(run_cmd([python, "-m", "pytest", "-q"], repo_path))

    if (repo_path / "pyproject.toml").exists():
        commands.append(run_cmd([python, "-m", "pip", "install", "ruff", "mypy"], repo_path))
        commands.append(run_cmd([python, "-m", "ruff", "check", "."], repo_path))

    return commands


def run_node_checks(repo_path: Path) -> List[CommandResult]:
    commands: List[CommandResult] = []
    npm = shutil.which("npm")
    if not npm:
        commands.append(
            CommandResult(
                command="npm",
                returncode=1,
                stdout="",
                stderr="npm not found in PATH",
                duration_seconds=0,
            )
        )
        return commands

    package_json = repo_path / "package.json"
    scripts = {}
    try:
        scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
    except Exception:
        pass

    if (repo_path / "package-lock.json").exists():
        commands.append(run_cmd([npm, "ci"], repo_path))
    else:
        commands.append(run_cmd([npm, "install"], repo_path))

    for script in ["lint", "test", "build"]:
        if script in scripts:
            commands.append(run_cmd([npm, "run", script], repo_path))

    return commands


def run_docker_checks(repo_path: Path) -> List[CommandResult]:
    commands: List[CommandResult] = []
    docker = shutil.which("docker")
    if not docker:
        commands.append(
            CommandResult(
                command="docker",
                returncode=1,
                stdout="",
                stderr="docker not found in PATH",
                duration_seconds=0,
            )
        )
        return commands

    if (repo_path / "Dockerfile").exists():
        commands.append(run_cmd([docker, "build", "-t", "repo-health-check:latest", "."], repo_path))
    return commands


def run_security_checks(repo_path: Path) -> Dict[str, List[CommandResult]]:
    results: Dict[str, List[CommandResult]] = {"python_deps": [], "node_deps": []}

    python = shutil.which("python") or shutil.which("py")
    if ((repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists()) and python:
        if shutil.which("pip-audit"):
            results["python_deps"].append(run_cmd(["pip-audit"], repo_path))
        else:
            install_result = run_cmd([python, "-m", "pip", "install", "pip-audit"], repo_path)
            results["python_deps"].append(install_result)
            if install_result.returncode == 0:
                results["python_deps"].append(run_cmd([python, "-m", "pip_audit"], repo_path))

    npm = shutil.which("npm")
    if (repo_path / "package.json").exists() and npm:
        results["node_deps"].append(run_cmd([npm, "audit", "--audit-level=high"], repo_path))

    return results


def detect_mobile_release_readiness(repo_path: Path) -> Dict[str, bool]:
    signals = {
        "android_project": (repo_path / "android").exists() or (repo_path / "build.gradle").exists(),
        "ios_project": (repo_path / "ios").exists() or bool(list(repo_path.glob("*.xcodeproj"))),
        "react_native": (repo_path / "react-native.config.js").exists(),
        "flutter": (repo_path / "pubspec.yaml").exists(),
        "capacitor": (repo_path / "capacitor.config.ts").exists() or (repo_path / "capacitor.config.json").exists(),
        "mobile_ci": (repo_path / ".github" / "workflows").exists()
        and any("android" in p.name.lower() or "ios" in p.name.lower() or "mobile" in p.name.lower() for p in (repo_path / ".github" / "workflows").glob("*.y*ml")),
        "release_docs": (repo_path / "RELEASE.md").exists() or (repo_path / "docs" / "release.md").exists(),
    }
    return signals


def compute_scores(checks: Dict[str, str], mobile_signals: Dict[str, bool]) -> tuple[int, int]:
    market_score = 50
    for name in ["python", "node", "docker", "ci_workflow", "python_deps", "node_deps"]:
        if checks.get(name) == "pass":
            market_score += 8
        elif checks.get(name) == "fail":
            market_score -= 10

    mobile_score = 0
    for enabled in mobile_signals.values():
        if enabled:
            mobile_score += 14
    mobile_score = min(mobile_score, 100)
    market_score = max(0, min(market_score, 100))
    return mobile_score, market_score


def get_default_branch(owner: str, repo: str, token: Optional[str]) -> str:
    url = f"{API_BASE}/repos/{owner}/{repo}"
    resp = github_get(url, token)
    return str(resp.json().get("default_branch", "main"))


def clone_or_update_repo(git: str, owner: str, repo: str, token: Optional[str], clone_dir: Path) -> tuple[Path, bool]:
    target = clone_dir / repo
    if token:
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    else:
        clone_url = f"https://github.com/{owner}/{repo}.git"
    if target.exists():
        fetch_result = run_cmd([git, "fetch", "--all", "--prune"], target)
        if fetch_result.returncode != 0:
            raise RuntimeError(f"git fetch failed: {fetch_result.stderr.strip()}")
        pull_result = run_cmd([git, "pull"], target)
        if pull_result.returncode != 0:
            raise RuntimeError(f"git pull failed: {pull_result.stderr.strip()}")
        return target, False

    clone_dir.mkdir(parents=True, exist_ok=True)
    clone_result = run_cmd([git, "clone", clone_url, str(target)], clone_dir)
    if clone_result.returncode != 0:
        raise RuntimeError(f"git clone failed: {clone_result.stderr.strip()}")
    return target, True


def run_fix_and_push(git: str, repo_path: Path, branch: str, push: bool) -> List[CommandResult]:
    commands: List[CommandResult] = []
    commands.append(run_cmd([git, "checkout", "-B", branch], repo_path))

    if (repo_path / "package.json").exists() and shutil.which("npm"):
        commands.append(run_cmd(["npm", "run", "lint", "--", "--fix"], repo_path))

    if (repo_path / "pyproject.toml").exists() and shutil.which("python"):
        commands.append(run_cmd(["python", "-m", "ruff", "check", ".", "--fix"], repo_path))

    commands.append(run_cmd([git, "add", "-A"], repo_path))
    diff_result = run_cmd([git, "diff", "--cached", "--name-only"], repo_path)
    commands.append(diff_result)
    if diff_result.stdout.strip():
        commands.append(run_cmd([git, "commit", "-m", "chore: production hardening auto-fixes"], repo_path))
        if push:
            commands.append(run_cmd([git, "push", "-u", "origin", branch], repo_path))

    return commands


def create_pull_request(
    owner: str,
    repo: str,
    token: Optional[str],
    head_branch: str,
    base_branch: str,
    title: str,
    body: str,
) -> str:
    url = f"{API_BASE}/repos/{owner}/{repo}/pulls"
    resp = github_post(
        url,
        token,
        {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
            "maintainer_can_modify": True,
        },
    )
    data = resp.json()
    return str(data.get("html_url", ""))


def evaluate_success(checks: Dict[str, str], commands: List[CommandResult], required_checks: List[str]) -> bool:
    for check_name in required_checks:
        if checks.get(check_name) != "pass":
            return False
    return all(c.returncode == 0 for c in commands if c.command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-repo GitHub hardening runner")
    parser.add_argument("--owner", required=True, help="GitHub owner or organization")
    parser.add_argument("--owner-type", default="auto", choices=["auto", "user", "org"], help="GitHub owner type")
    parser.add_argument("--repo", action="append", default=[], help="Specific repository name (repeatable)")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Environment variable containing GitHub token")
    parser.add_argument("--include-private", action="store_true", help="Include private repositories (requires token)")
    parser.add_argument("--clone-dir", default="_repo_hardening", help="Directory for local clones")
    parser.add_argument("--fix", action="store_true", help="Run auto-fix actions where available")
    parser.add_argument("--push", action="store_true", help="Push fix branch after commit")
    parser.add_argument("--create-pr", action="store_true", help="Create pull requests after pushing fix branch")
    parser.add_argument("--pr-base", default="main", help="PR base branch")
    parser.add_argument("--fix-branch", default="chore/production-hardening", help="Branch name for fixes")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker checks")
    parser.add_argument("--skip-security", action="store_true", help="Skip dependency security checks")
    parser.add_argument("--skip-mobile-check", action="store_true", help="Skip mobile release readiness scoring")
    parser.add_argument("--policy-file", default="scripts/repo_hardening_policy.json", help="Policy file path")
    parser.add_argument("--report", default="repo_hardening_report.json", help="Output report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv(args.token_env)
    if not token:
        print(f"Warning: missing {args.token_env}. Running in unauthenticated mode (public repositories only).")
    if args.include_private and not token:
        print("Error: --include-private requires an authenticated token with repo access")
        return 2

    try:
        git = locate_git()
    except FileNotFoundError as exc:
        print(str(exc))
        return 2

    policy = load_policy(Path(args.policy_file))
    required_checks = list(policy.get("required_checks", ["ci_workflow"]))
    security_checks = list(policy.get("security_checks", ["python_deps", "node_deps"]))
    pr_policy = policy.get("pr", {})
    leadership_policy = policy.get("market_leadership", {})

    repos = args.repo or list_repos(
        args.owner,
        token,
        owner_type=args.owner_type,
        include_private=args.include_private,
    )
    if not repos:
        print("No repositories found.")
        return 1

    clone_dir = Path(args.clone_dir).resolve()
    reports: List[RepoReport] = []

    for repo in repos:
        print(f"\n=== Processing {repo} ===")
        notes: List[str] = []
        commands: List[CommandResult] = []
        pr_url: Optional[str] = None

        try:
            repo_path, cloned = clone_or_update_repo(git, args.owner, repo, token, clone_dir)
        except Exception as exc:
            reports.append(
                RepoReport(
                    repo=repo,
                    path=str(clone_dir / repo),
                    cloned=False,
                    checks={"clone": "fail"},
                    commands=[],
                    success=False,
                    notes=[f"clone/update failed: {exc}"],
                )
            )
            continue

        checks = detect_checks(repo_path)

        if checks["python"] == "pending":
            py_results = run_python_checks(repo_path)
            commands.extend(py_results)
            checks["python"] = "pass" if all(c.returncode == 0 for c in py_results) else "fail"

        if checks["node"] == "pending":
            node_results = run_node_checks(repo_path)
            commands.extend(node_results)
            checks["node"] = "pass" if all(c.returncode == 0 for c in node_results) else "fail"

        if checks["docker"] == "pending":
            if args.skip_docker:
                checks["docker"] = "skip"
            else:
                docker_results = run_docker_checks(repo_path)
                commands.extend(docker_results)
                checks["docker"] = "pass" if all(c.returncode == 0 for c in docker_results) else "fail"

        if not args.skip_security:
            security_results = run_security_checks(repo_path)
            for check_name in ["python_deps", "node_deps"]:
                check_results = security_results.get(check_name, [])
                commands.extend(check_results)
                if check_results:
                    checks[check_name] = "pass" if all(c.returncode == 0 for c in check_results) else "fail"
                elif check_name in security_checks:
                    checks[check_name] = "skip"

        if args.fix:
            fix_results = run_fix_and_push(git, repo_path, args.fix_branch, args.push)
            commands.extend(fix_results)
            notes.append("auto-fix mode enabled")

            wants_pr = bool(args.create_pr or pr_policy.get("create", False))
            if wants_pr and args.push:
                try:
                    title_prefix = str(pr_policy.get("title_prefix", "chore: production hardening for"))
                    pr_title = f"{title_prefix} {repo}"
                    pr_body = (
                        "Automated production hardening updates generated by scripts/harden_github_repos.py\n\n"
                        "Please review test, lint, and deployment impacts before merge."
                    )
                    pr_base = str(pr_policy.get("base", args.pr_base))
                    if pr_base == "main":
                        pr_base = get_default_branch(args.owner, repo, token)
                    pr_url = create_pull_request(
                        owner=args.owner,
                        repo=repo,
                        token=token,
                        head_branch=args.fix_branch,
                        base_branch=pr_base,
                        title=pr_title,
                        body=pr_body,
                    )
                except Exception as exc:
                    notes.append(f"pull request creation failed: {exc}")
            elif wants_pr and not args.push:
                notes.append("pull request creation skipped because --push was not set")

        mobile_signals = {} if args.skip_mobile_check else detect_mobile_release_readiness(repo_path)
        mobile_score, market_score = compute_scores(checks, mobile_signals)
        min_score = int(leadership_policy.get("minimum_score", 70))
        require_mobile = bool(leadership_policy.get("require_mobile_release_readiness", True))
        if market_score < min_score:
            notes.append(f"market leadership score below target: {market_score} < {min_score}")
        if require_mobile and mobile_score < 40:
            notes.append("mobile release readiness below threshold for app/play store release")

        success = evaluate_success(checks, commands, required_checks=required_checks)
        if market_score < min_score:
            success = False
        if require_mobile and mobile_score < 40:
            success = False

        reports.append(
            RepoReport(
                repo=repo,
                path=str(repo_path),
                cloned=cloned,
                checks=checks,
                commands=commands,
                success=success,
                notes=notes,
                pr_url=pr_url,
                mobile_readiness_score=mobile_score,
                market_leadership_score=market_score,
            )
        )

    report_data = {
        "owner": args.owner,
        "owner_type": args.owner_type,
        "include_private": args.include_private,
        "policy_file": args.policy_file,
        "required_checks": required_checks,
        "security_checks": security_checks,
        "repo_count": len(reports),
        "success_count": sum(1 for r in reports if r.success),
        "failure_count": sum(1 for r in reports if not r.success),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reports": [
            {
                **asdict(report),
                "commands": [asdict(c) for c in report.commands],
            }
            for report in reports
        ],
    }

    Path(args.report).write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(f"\nSaved report to {args.report}")
    print(
        f"Summary: {report_data['success_count']} succeeded, "
        f"{report_data['failure_count']} failed, out of {report_data['repo_count']}"
    )

    return 0 if report_data["failure_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
