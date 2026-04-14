const BASE_URL = process.env.PERF_BASE_URL || 'http://localhost:8080';
const MAX_P95_MS = Number(process.env.PERF_MAX_P95_MS || 1800);
const ITERATIONS = Number(process.env.PERF_ITERATIONS || 30);

async function measure(path) {
  const samples = [];
  for (let i = 0; i < ITERATIONS; i += 1) {
    const t0 = performance.now();
    const res = await fetch(`${BASE_URL}${path}`);
    if (!res.ok) {
      throw new Error(`non_2xx:${path}:${res.status}`);
    }
    const t1 = performance.now();
    samples.push(t1 - t0);
  }
  samples.sort((a, b) => a - b);
  const idx = Math.min(samples.length - 1, Math.floor(0.95 * samples.length));
  return { path, p95: samples[idx], avg: samples.reduce((a, b) => a + b, 0) / samples.length };
}

const criticalPaths = ['/health', '/api/meta/brand'];

const results = [];
for (const path of criticalPaths) {
  results.push(await measure(path));
}

let failed = false;
for (const r of results) {
  console.log(`${r.path} avg=${r.avg.toFixed(1)}ms p95=${r.p95.toFixed(1)}ms`);
  if (r.p95 > MAX_P95_MS) failed = true;
}

if (failed) {
  console.error(`Performance gate failed: p95 above ${MAX_P95_MS}ms`);
  process.exit(1);
}

console.log('Performance gate passed');
