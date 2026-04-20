import { ChatOpenAI } from '@langchain/openai';
import { z } from 'zod';
import { prisma } from '../../db.js';

const SuggestionSchema = z.object({
  appSlug: z.string(),
  title: z.string(),
  rationale: z.string(),
  recommendedDiff: z.string(),
});

type Suggestion = z.infer<typeof SuggestionSchema>;

export async function runSupervisorCycle() {
  const [metrics, feedback] = await Promise.all([
    prisma.appMetric.findMany({ orderBy: { createdAt: 'desc' }, take: 50 }),
    prisma.userFeedback.findMany({ orderBy: { createdAt: 'desc' }, take: 50 }),
  ]);

  const llm = new ChatOpenAI({ model: 'gpt-4o-mini', temperature: 0.1 });

  const prompt = `You are an autonomous platform engineer. Based on metrics and feedback, propose exactly one high-impact improvement as strict JSON with keys appSlug,title,rationale,recommendedDiff. Metrics: ${JSON.stringify(metrics)} Feedback: ${JSON.stringify(feedback)}`;
  const res = await llm.invoke(prompt);

  let parsed: Suggestion;
  try {
    parsed = SuggestionSchema.parse(JSON.parse(String(res.content)));
  } catch {
    parsed = {
      appSlug: 'autonomous-trading-coach',
      title: 'Fallback improvement: tighten model drift alerts',
      rationale: 'LLM output parse failed; queued deterministic hardening step.',
      recommendedDiff: 'Add stricter p95 alerting and stale model lockout in inference route.',
    };
  }

  const saved = await prisma.workforceSuggestion.create({
    data: {
      appSlug: parsed.appSlug,
      title: parsed.title,
      rationale: parsed.rationale,
      recommendedDiff: parsed.recommendedDiff,
      status: 'PENDING_REVIEW',
    },
  });

  return saved;
}
