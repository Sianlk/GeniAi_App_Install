# GeniAi_App_Install
![Auto Fix](https://github.com/Sianlk/GeniAi_App_Install/actions/workflows/auto-fix-node.yml/badge.svg)
![Conflict Resolver](https://github.com/Sianlk/GeniAi_App_Install/actions/workflows/conflict-resolver.yml/badge.svg)
# Genesis AI Empire

## Modules
- core/analytics
- core/ar_vr
- core/robotics
- core/ai_models
- core/viral
- core/monetization

## Deployment
- Docker: docker-compose up
- Kubernetes: kubectl apply -f k8s/kubernetes.yaml
- CI/CD: GitHub Actions .github/workflows/

## Multi-Repo Production Hardening
Use the script below to audit and improve repositories under a GitHub user or organization.

1. Install Git for Windows:
	- winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
2. Create a GitHub token with repo permissions and set it in your shell:
	- $env:GITHUB_TOKEN="YOUR_TOKEN"
3. Run the hardening pass for all repositories:
	- python scripts/harden_github_repos.py --owner YOUR_GITHUB_OWNER --token-env GITHUB_TOKEN
4. Include private repositories (token with repo scope required):
	- python scripts/harden_github_repos.py --owner YOUR_GITHUB_OWNER --include-private --token-env GITHUB_TOKEN

5. Optional: enable auto-fixes and push a hardening branch:
	- python scripts/harden_github_repos.py --owner YOUR_GITHUB_OWNER --fix --push

6. Optional: for organizations, set owner type explicitly:
	- python scripts/harden_github_repos.py --owner YOUR_ORG --owner-type org

7. Optional: auto-create pull requests after pushing fixes:
	- python scripts/harden_github_repos.py --owner YOUR_GITHUB_OWNER --fix --push --create-pr

8. Optional: include security and mobile-store readiness gates:
	- python scripts/harden_github_repos.py --owner YOUR_GITHUB_OWNER --fix --push --create-pr

Generated report:
- repo_hardening_report.json

Policy file:
- scripts/repo_hardening_policy.json
- Set required checks and default PR behavior centrally for all repositories.
- Set security checks and market leadership score thresholds.

The report includes clone status, Python/Node/Docker check results, dependency security checks, CI workflow presence, mobile readiness score, market leadership score, executed commands, and pass/fail per repository.

## Baseline Standards PR Automation
Use this to automatically add missing baseline files across repositories and open PRs.

1. Set token:
	- $env:GITHUB_TOKEN="YOUR_TOKEN"
2. Dry-run plan (no changes):
	- python scripts/standardize_repos.py --owner YOUR_GITHUB_OWNER --owner-type user
3. Apply changes and create PRs:
	- python scripts/standardize_repos.py --owner YOUR_GITHUB_OWNER --owner-type user --apply
4. Include private repositories:
	- python scripts/standardize_repos.py --owner YOUR_GITHUB_OWNER --owner-type user --include-private --apply

The script can add these missing files when not present:
- .github/workflows/release-quality.yml
- SECURITY.md
- RELEASE.md
- LICENSE

## Portfolio Market Leadership Scan
Scan all repositories under an owner and generate ranked pivots without cloning.

1. Run scan:
	- python scripts/scan_market_leadership.py --owner YOUR_GITHUB_OWNER --owner-type user
2. Output report:
	- portfolio_market_readiness.json

This report ranks repos by readiness score and provides prioritized enhancement pivots for engineering quality, security, observability, release process, and growth moat strategy.

## Max Enhancement Executor
Apply the strongest baseline enhancement pack across all repositories and open PRs.

1. Dry run (plan only):
	- python scripts/apply_max_enhancements.py --owner YOUR_GITHUB_OWNER --owner-type user
2. Apply to all repositories and create PRs:
	- python scripts/apply_max_enhancements.py --owner YOUR_GITHUB_OWNER --owner-type user --apply
3. Include private repositories:
	- python scripts/apply_max_enhancements.py --owner YOUR_GITHUB_OWNER --owner-type user --include-private --apply

Generated report:
- max_enhancement_report.json

Enhancement pack includes quality CI, security scanning, release governance, code ownership, contribution standards, observability baseline, go-to-market playbook, mobile store checklist, and license baseline.
