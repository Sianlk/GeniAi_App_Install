#!/usr/bin/env node
/**
 * chaos_harness.mjs
 * Load + chaos test for GeniAi unified backend.
 *
 * Usage:
 *   JWT=<token> BASE_URL=http://localhost:3000 node scripts/chaos_harness.mjs
 *
 * What it does:
 *  1. Floods /health + /api/apps/predict for 60s (configurable)
 *  2. Records p95/p99 latencies per endpoint
 *  3. Injects artificial load spikes every 10s to surface 429 behaviour
 *  4. Pushes AppMetric rows via /api/metrics/ingest for AI workforce context
 *  5. Triggers workforce supervisor cycle via /api/workforce/run
 *  6. Exits 1 if any p95 breaches SLO (default 1800ms)
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';
const JWT = process.env.JWT ?? '';
const DURATION_MS = Number(process.env.DURATION_MS ?? 60_000);
const CONCURRENCY = Number(process.env.CONCURRENCY ?? 10);
const P95_SLO_MS = Number(process.env.P95_SLO_MS ?? 1800);

if (!JWT) {
  console.error('ERROR: JWT env var required. Run: JWT=<your-token> node scripts/chaos_harness.mjs');
  process.exit(1);
}

const authHeaders = {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${JWT}`
};

/** Measure a single request, returning latency in ms */
async function measure(url, options = {}) {
  const t = Date.now();
  const res = await fetch(url, options).catch(() => ({ status: 0 }));
  return { latency: Date.now() - t, status: res.status };
}

/** Compute percentile from sorted numeric array */
function percentile(sorted, p) {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}

const results = {
  health: [],
  predict: [],
  metricsIngest: []
};

let running = true;
let requests = 0;
let errors = 0;

/** Run CONCURRENCY workers for DURATION_MS */
async function worker() {
  while (running) {
    const endpoint = ['health', 'predict', 'metricsIngest'][Math.floor(Math.random() * 3)];

    let r;
    if (endpoint === 'health') {
      r = await measure(`${BASE_URL}/health`);
    } else if (endpoint === 'predict') {
      r = await measure(`${BASE_URL}/api/apps/predict`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ appSlug: 'autonomous-trading-coach', input: 'chaos-test' })
      });
    } else {
      r = await measure(`${BASE_URL}/api/metrics/ingest`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          metrics: [
            { appSlug: 'autonomous-trading-coach', metricName: 'chaos_latency_ms', metricVal: Math.random() * 2000 },
            { appSlug: 'autonomous-trading-coach', metricName: 'chaos_error_rate', metricVal: Math.random() }
          ]
        })
      });
    }

    results[endpoint].push(r.latency);
    requests++;
    if (r.status === 0 || r.status >= 500) errors++;
  }
}

/** Every 10s, send a spike burst of 50 concurrent /health requests to surface rate-limiting */
async function spikeBurst() {
  const spike = await Promise.all(
    Array.from({ length: 50 }, () => measure(`${BASE_URL}/health`))
  );
  const hit429 = spike.filter(r => r.status === 429).length;
  console.log(`  [spike] 50 concurrent /health — 429s: ${hit429}`);
}

console.log(`\nGeniAi Chaos Harness`);
console.log(`  Base URL  : ${BASE_URL}`);
console.log(`  Duration  : ${DURATION_MS / 1000}s`);
console.log(`  Concurrency: ${CONCURRENCY} workers`);
console.log(`  P95 SLO   : ${P95_SLO_MS}ms`);
console.log(`  Starting...\n`);

const workers = Array.from({ length: CONCURRENCY }, () => worker());
const spikeInterval = setInterval(spikeBurst, 10_000);

await new Promise(resolve => setTimeout(resolve, DURATION_MS));
running = false;
clearInterval(spikeInterval);
await Promise.all(workers);

// Compute p95/p99 per endpoint
let sloViolation = false;
const report = [];

for (const [name, latencies] of Object.entries(results)) {
  if (latencies.length === 0) continue;
  const sorted = [...latencies].sort((a, b) => a - b);
  const p95 = percentile(sorted, 95);
  const p99 = percentile(sorted, 99);
  const avg = Math.round(sorted.reduce((a, b) => a + b, 0) / sorted.length);
  const violation = p95 > P95_SLO_MS;
  if (violation) sloViolation = true;

  report.push({ endpoint: name, count: latencies.length, avg_ms: avg, p95_ms: p95, p99_ms: p99, slo_ok: !violation });
}

console.log('\n=== Chaos Harness Report ===');
console.log(`Total requests : ${requests}`);
console.log(`Errors (5xx/net): ${errors}`);
console.table(report);

// Trigger workforce supervisor to ingest the chaos metrics
try {
  const sup = await fetch(`${BASE_URL}/api/workforce/run`, {
    method: 'POST',
    headers: authHeaders
  });
  const supBody = await sup.json().catch(() => ({}));
  console.log(`\nWorkforce supervisor cycle: ${sup.status}`, supBody);
} catch (e) {
  console.warn('Workforce supervisor trigger failed (non-fatal):', e.message);
}

if (sloViolation) {
  console.error('\nSLO VIOLATION: p95 exceeded threshold on at least one endpoint');
  process.exit(1);
} else {
  console.log('\nAll SLOs met. ✓');
}
