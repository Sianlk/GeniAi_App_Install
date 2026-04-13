#!/usr/bin/env bash
set -euo pipefail

APPS=(
  sianlk-core
  geniai-persona-studio
  ai-aesthetics-lab
  ai-business-brain
  aiblty-coach
  aibltycode-studio
  buildquote-pro
  comppropdata-intelligence
  terminalai-ops
  gitgit-copilot
  autonomous-trading-coach
)

for app in "${APPS[@]}"; do
  echo "Building $app via EAS"
  pushd "mobile/apps/$app" >/dev/null
  npx eas build --platform all --profile production --non-interactive
  npx eas submit --platform android --profile production --non-interactive
  npx eas submit --platform ios --profile production --non-interactive
  popd >/dev/null
done

echo "All 11 app builds submitted."
