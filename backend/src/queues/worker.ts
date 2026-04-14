import { Worker } from 'bullmq';
import { Octokit } from '@octokit/rest';
import { redis } from '../redis.js';
import { prisma } from '../db.js';
import { env } from '../config.js';

const octokit = env.GITHUB_TOKEN ? new Octokit({ auth: env.GITHUB_TOKEN }) : null;

async function openDraftPR(suggestionId: string) {
  const suggestion = await prisma.workforceSuggestion.findUniqueOrThrow({ where: { id: suggestionId } });

  if (!octokit) {
    await prisma.workforceSuggestion.update({
      where: { id: suggestion.id },
      data: { status: 'MANUAL_REVIEW_REQUIRED' }
    });
    return;
  }

  const title = `[AI Workforce] ${suggestion.title}`;
  const body = `## AI Workforce Suggestion\n\n**App**: ${suggestion.appSlug}\n\n**Rationale**:\n${suggestion.rationale}\n\n**Suggested Diff**:\n\n\`\`\`\n${suggestion.recommendedDiff}\n\`\`\`\n\nRequires super-admin approval before merge.`;

  await octokit.issues.create({
    owner: env.GITHUB_OWNER,
    repo: env.GITHUB_REPO,
    title,
    body,
    labels: ['ai-workforce', 'needs-review']
  });

  await prisma.workforceSuggestion.update({
    where: { id: suggestion.id },
    data: { status: 'ISSUE_OPENED' }
  });
}

new Worker(
  'workforce-tasks',
  async (job) => {
    if (job.name === 'open-pr-task') {
      await openDraftPR(job.data.suggestionId as string);
    }
  },
  { connection: redis }
);

console.log('workforce worker online');
