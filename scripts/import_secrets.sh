#!/usr/bin/env bash
set -euo pipefail

SOURCE_FILE="${1:-.secrets.local.env}"
TARGET_FILE="${2:-.env}"

required=(
  DIGITALOCEAN_ACCESS_TOKEN
  DIGITALOCEAN_APP_ID
  OPENAI_API_KEY
  GITHUB_TOKEN
  SNYK_TOKEN
  STRIPE_SECRET_KEY
  STRIPE_WEBHOOK_SECRET
)

placeholder_re='xxx|\.\.\.|changeme|replace_me|token_here|app-xxxx|^sk-xxx$|^ghp_xxx$|^snyk_xxx$|^dop_v1_xxx$|<|>'

declare -A source_map
if [[ -f "$SOURCE_FILE" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    source_map["$key"]="$val"
  done < "$SOURCE_FILE"
fi

if [[ -f "$TARGET_FILE" ]]; then
  mapfile -t target_lines < "$TARGET_FILE"
else
  target_lines=()
fi

updated=0
found=0

for key in "${required[@]}"; do
  candidate="${source_map[$key]-${!key-}}"

  if [[ -z "$candidate" || "$candidate" =~ $placeholder_re ]]; then
    continue
  fi

  found=$((found + 1))
  newline="$key=$candidate"
  matched=0

  for i in "${!target_lines[@]}"; do
    if [[ "${target_lines[$i]}" =~ ^${key}= ]]; then
      target_lines[$i]="$newline"
      matched=1
      updated=$((updated + 1))
      break
    fi
  done

  if [[ "$matched" -eq 0 ]]; then
    target_lines+=("$newline")
    updated=$((updated + 1))
  fi

  export "$key=$candidate"
done

printf "%s\n" "${target_lines[@]}" > "$TARGET_FILE"
echo "Secrets imported. candidates_found=$found lines_updated=$updated"
