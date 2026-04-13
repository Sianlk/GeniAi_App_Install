# Unified 11-App AI Ecosystem

Production-ready monorepo blueprint for 11 cross-platform apps (iOS, Android, Web via Expo) sharing one backend on DigitalOcean.

## Stack
- Backend: Node.js, Fastify, Prisma, PostgreSQL, Redis, BullMQ, LangChain, Zod
- Mobile/Web: Expo + React Native + TensorFlow.js + Three.js
- Admin UI: AdminJS + custom super-admin endpoints
- Security: Helmet, CORS policy, rate limiting, JWT rotation, audit logs, Snyk scanning
- CI/CD: GitHub Actions -> Docker build -> DigitalOcean deploy
- Monetization: Stripe Connect GBP + unified credits ledger + monthly 5% compound rewards

## 11 Apps
1. Sianlk Core Workspace
2. GeniAI Persona Studio
3. AI Aesthetics Lab
4. AI Business Brain
5. Aiblty Coach
6. AibltyCode Studio
7. BuildQuote Pro
8. CompPropData Intelligence
9. TerminalAI Ops
10. GitGit Copilot
11. Autonomous Trading Coach (complex template included)

Each app receives one or more unfair-advantage capabilities:
- real-time collaboration with WebSockets
- offline-first sync and conflict resolution
- predictive inference with TensorFlow.js
- immersive AR/3D visualizations with React Three Fiber

## Super Admin
Hardcoded super admin identity: `hosturserver@gmail.com`
- full user control across all apps
- per-user/per-app feature injection
- live logs and AI workforce suggestions
- immutable audit trail

## Quick Start
```bash
cp .env.example .env
cd backend
npm install
npm run prisma:generate
npm run prisma:migrate
cd ..
docker compose up --build -d
```

## Deploy to DigitalOcean
```bash
bash scripts/deploy_digitalocean.sh
```

## CI/CD
- `.github/workflows/ci-cd.yml` builds backend and mobile matrix
- deploys unified stack to DigitalOcean App Platform on push to `main`
- runs Snyk dependency scan and fails build on high severity

## App Factory
Create/fork all app packages from template:
```bash
node scripts/scaffold-apps.mjs
```
