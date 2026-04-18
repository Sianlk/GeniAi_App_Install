import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../../db.js';

const MetricRow = z.object({
  appSlug: z.string().min(2),
  metricName: z.string().min(2),
  metricVal: z.number(),
  tags: z.record(z.unknown()).optional(),
});

const MetricsBatch = z.object({
  metrics: z.array(MetricRow).min(1).max(500),
});

export async function metricsRoutes(app: FastifyInstance) {
  /**
   * POST /api/metrics/ingest
   * Authenticated. Accepts up to 500 metric rows per call.
   * Used by mobile apps and internal monitors to feed AI workforce context.
   */
  app.post(
    '/api/metrics/ingest',
    {
      preHandler: [app.authenticate],
    },
    async (req, reply) => {
      const { metrics } = MetricsBatch.parse(req.body);

      const rows = await prisma.$transaction(
        metrics.map((m) =>
          prisma.appMetric.create({
            data: {
              appSlug: m.appSlug,
              metricName: m.metricName,
              metricVal: m.metricVal,
              tags: (m.tags ?? {}) as object,
            },
          }),
        ),
      );

      return { ingested: rows.length };
    },
  );

  /**
   * GET /api/metrics/summary/:appSlug
   * Super admin only — aggregate recent metrics for AI workforce context.
   */
  app.get(
    '/api/metrics/summary/:appSlug',
    {
      preHandler: [app.authenticate],
    },
    async (req, reply) => {
      const actor = req.user as { role: string };
      if (actor.role !== 'SUPER_ADMIN') {
        return reply.code(403).send({ error: 'forbidden' });
      }

      const { appSlug } = req.params as { appSlug: string };

      const rows = await prisma.appMetric.groupBy({
        by: ['metricName'],
        where: {
          appSlug,
          createdAt: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) },
        },
        _avg: { metricVal: true },
        _max: { metricVal: true },
        _min: { metricVal: true },
        _count: { metricVal: true },
      });

      return { appSlug, window: '24h', metrics: rows };
    },
  );
}
