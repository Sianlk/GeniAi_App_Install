import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../../db.js';

const SyncPush = z.object({
  appSlug: z.string().min(2),
  deviceId: z.string().min(3),
  events: z.array(
    z.object({
      eventType: z.string().min(2),
      payload: z.unknown(),
      clientTs: z.string().datetime(),
      conflictKey: z.string().optional()
    })
  ).min(1)
});

const SyncPull = z.object({
  appSlug: z.string().min(2),
  afterTs: z.string().datetime().optional()
});

export async function syncRoutes(app: FastifyInstance) {
  app.post('/api/sync/push', { preHandler: [app.authenticate] }, async (req) => {
    const user = req.user as { userId: string };
    const input = SyncPush.parse(req.body);

    const writes = await Promise.all(
      input.events.map(async (evt) => {
        let resolved = true;
        if (evt.conflictKey) {
          const existing = await prisma.offlineSyncEvent.findFirst({
            where: {
              userId: user.userId,
              appSlug: input.appSlug,
              conflictKey: evt.conflictKey,
              resolved: true
            },
            orderBy: { serverTs: 'desc' }
          });

          resolved = !existing || new Date(evt.clientTs) >= existing.serverTs;
        }

        return prisma.offlineSyncEvent.create({
          data: {
            userId: user.userId,
            appSlug: input.appSlug,
            deviceId: input.deviceId,
            eventType: evt.eventType,
            payload: evt.payload as object,
            clientTs: new Date(evt.clientTs),
            conflictKey: evt.conflictKey,
            resolved
          }
        });
      })
    );

    return { accepted: writes.length };
  });

  app.post('/api/sync/pull', { preHandler: [app.authenticate] }, async (req) => {
    const user = req.user as { userId: string };
    const input = SyncPull.parse(req.body);
    const after = input.afterTs ? new Date(input.afterTs) : new Date(0);

    const rows = await prisma.offlineSyncEvent.findMany({
      where: {
        userId: user.userId,
        appSlug: input.appSlug,
        serverTs: { gt: after },
        resolved: true
      },
      orderBy: { serverTs: 'asc' },
      take: 1000
    });

    return {
      events: rows,
      nextCursor: rows.length ? rows[rows.length - 1].serverTs.toISOString() : after.toISOString()
    };
  });
}
