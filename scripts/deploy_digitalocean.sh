#!/usr/bin/env bash
set -euo pipefail

if { [ -z "${DIGITALOCEAN_ACCESS_TOKEN:-}" ] || [ -z "${DIGITALOCEAN_APP_ID:-}" ]; } && [ -f .env ]; then
  set -a
  source .env
  set +a
fi

if [ -z "${DIGITALOCEAN_ACCESS_TOKEN:-}" ] || [ -z "${DIGITALOCEAN_APP_ID:-}" ]; then
  echo "DIGITALOCEAN_ACCESS_TOKEN and DIGITALOCEAN_APP_ID are required"
  exit 1
fi

if [[ "${DIGITALOCEAN_ACCESS_TOKEN}" =~ xxx|\.\.\.|changeme|replace_me|token_here|dop_v1_xxx ]] || [[ "${DIGITALOCEAN_APP_ID}" =~ xxx|\.\.\.|changeme|replace_me|token_here|app-xxxx ]]; then
  echo "DigitalOcean secrets look like placeholders; aborting deployment"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required"
  exit 1
fi

echo "Building and pushing backend container..."
docker compose build backend workforce

echo "Triggering DigitalOcean App Platform deployment..."
deploy_json=$(curl -sS -X POST \
  "https://api.digitalocean.com/v2/apps/${DIGITALOCEAN_APP_ID}/deployments" \
  -H "Authorization: Bearer ${DIGITALOCEAN_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"force_build":true}')

deployment_id=$(echo "$deploy_json" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p' | head -n1)
if [ -z "$deployment_id" ]; then
  echo "failed to parse deployment id"
  echo "$deploy_json"
  exit 1
fi

echo "Deployment id: $deployment_id"
echo "Polling deployment status..."

for _ in $(seq 1 60); do
  status_json=$(curl -sS \
    "https://api.digitalocean.com/v2/apps/${DIGITALOCEAN_APP_ID}/deployments/${deployment_id}" \
    -H "Authorization: Bearer ${DIGITALOCEAN_ACCESS_TOKEN}")

  phase=$(echo "$status_json" | sed -n 's/.*"phase":"\([^"]*\)".*/\1/p' | head -n1)
  echo "phase=$phase"

  if [ "$phase" = "ACTIVE" ]; then
    echo "Deployment succeeded"
    exit 0
  fi

  if [ "$phase" = "ERROR" ] || [ "$phase" = "CANCELED" ]; then
    echo "Deployment failed"
    echo "$status_json"
    exit 1
  fi

  sleep 10
done

echo "Deployment polling timed out"
exit 1
