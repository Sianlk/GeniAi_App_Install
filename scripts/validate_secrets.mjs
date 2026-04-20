#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);

function getArg(name, fallback) {
  const idx = args.indexOf(name);
  if (idx === -1 || idx + 1 >= args.length) return fallback;
  return args[idx + 1];
}

const profile = getArg('--profile', 'runtime');
const envFile = path.resolve(process.cwd(), getArg('--env-file', '.env'));

const requiredProfiles = {
  runtime: [
    'DATABASE_URL',
    'REDIS_URL',
    'JWT_ACCESS_SECRET',
    'JWT_REFRESH_SECRET',
    'LOGO_URL',
    'SUPER_ADMIN_EMAIL',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'OPENAI_API_KEY'
  ],
  deploy: [
    'DIGITALOCEAN_ACCESS_TOKEN',
    'DIGITALOCEAN_APP_ID',
    'GITHUB_TOKEN',
    'SNYK_TOKEN'
  ]
};

if (!requiredProfiles[profile]) {
  console.error(`Unknown profile '${profile}'. Use runtime|deploy`);
  process.exit(2);
}

const placeholderRe = /xxx|\.\.\.|changeme|replace_me|token_here|app-xxxx|^sk-xxx$|^ghp_xxx$|^snyk_xxx$|^dop_v1_xxx$|<|>/i;

function parseEnvFile(file) {
  if (!fs.existsSync(file)) return {};
  const out = {};
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
  for (const line of lines) {
    if (!line || line.trim().startsWith('#')) continue;
    const idx = line.indexOf('=');
    if (idx <= 0) continue;
    const key = line.slice(0, idx).trim();
    const val = line.slice(idx + 1).trim();
    out[key] = val;
  }
  return out;
}

const envFileMap = parseEnvFile(envFile);

function effectiveValue(key) {
  if (process.env[key] && process.env[key].trim()) return process.env[key].trim();
  return envFileMap[key] ?? '';
}

const required = requiredProfiles[profile];
const missing = [];
const placeholder = [];

for (const key of required) {
  const value = effectiveValue(key);
  if (!value) {
    missing.push(key);
    continue;
  }
  if (placeholderRe.test(value)) {
    placeholder.push(key);
  }
}

if (missing.length || placeholder.length) {
  console.error(`Secret validation failed for profile '${profile}'.`);
  if (missing.length) {
    console.error(`Missing: ${missing.join(', ')}`);
  }
  if (placeholder.length) {
    console.error(`Placeholder-like values: ${placeholder.join(', ')}`);
  }
  process.exit(1);
}

console.log(`Secret validation passed for profile '${profile}'.`);
