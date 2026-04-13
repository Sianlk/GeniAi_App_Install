# Production Technical Blueprint

## 1) System Topology
- One shared backend (`backend`) serving all 11 apps.
- PostgreSQL for canonical data and audit logs.
- Redis + BullMQ for asynchronous AI workforce jobs.
- Nginx edge proxy for HTTP termination and routing.
- Expo app fleet generated from one advanced template.

## 2) Competitive Advantage Matrix
1. sianlk-core: unified command center + realtime ops websocket
2. geniai-persona-studio: adaptive persona memory + offline replay
3. ai-aesthetics-lab: on-device inference + AR result overlays
4. ai-business-brain: predictive opportunity scoring + live signal stream
5. aiblty-coach: personal model drift detection + rewards loop
6. aibltycode-studio: proactive static-analysis copilots + realtime pair coding
7. buildquote-pro: probabilistic pricing engine + geospatial 3D estimates
8. comppropdata-intelligence: forecast blending + anomaly detection
9. terminalai-ops: command graphing + offline-first runbook cache
10. gitgit-copilot: merge-risk prediction + websocket review rooms
11. autonomous-trading-coach: TensorFlow.js alpha model + low-latency stream + offline strategy queue

## 3) AI Workforce (Self-Evolving)
- Supervisor reads metrics + user feedback and proposes improvements.
- Suggestions are persisted as `WorkforceSuggestion` entries.
- Dual-control approval flow:
  - admin requests approval
  - super admin approves
  - queue executes issue/PR creation only after approval
- BullMQ worker opens tracked engineering items in GitHub after approval.
- Super admin (`hosturserver@gmail.com`) remains the final merge authority.

## 4) Super Admin Capability
- Hardcoded super-admin email in backend config and checks.
- Can list and control users, issue feature overrides, inspect logs, run workforce cycles.
- Every admin action is written to immutable audit logs.

## 5) Monetization and Ledger (GBP)
- Stripe Connect checkout for credit purchase in GBP.
- `CreditTxn` records all ledger events.
- Monthly 5% compound rewards applied by SQL scheduled function (`backend/sql/credit_compounding.sql`).

## 6) Cybersecurity Controls
- OWASP mitigations included:
  - secure headers via Helmet
  - strict CORS policy
  - API rate limiting
  - JWT access + refresh rotation
  - parameterized ORM access via Prisma
  - audit logs for admin actions
  - Snyk dependency scanning in CI
  - authenticated websocket channels with app-scoped ACL checks
  - offline sync conflict resolution and immutable sync event trail

## 8) SLO Guardrails
- CI includes p95 latency gate for critical endpoints.
- Deployment is blocked if p95 exceeds configured threshold.
- Threshold defaults: p95 <= 1800ms on `/health` and `/api/meta/brand`.

## 7) Deployment
- `docker-compose.yml` for full stack local/prod parity.
- `.github/workflows/ci-cd.yml` for quality, security scan, deployment trigger.
- `.do/app.yaml` for DigitalOcean App Platform deploy spec.
- `scripts/deploy_digitalocean.sh` for manual forced deployments.
