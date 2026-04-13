import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../../db.js';
import { requireAdminOrSuper, requireSuperAdmin } from '../../middleware/authz.js';
import { writeAuditLog } from '../../middleware/audit.js';
import { workforceQueue } from '../../queues/queue.js';
import { generateApprovalSignature, verifyApprovalSignature } from './signed-approval.js';
import { env } from '../../config.js';

const OverrideInput = z.object({
  userId: z.string().uuid().optional(),
  appSlug: z.string().min(2),
  featureKey: z.string().min(2),
  featureValue: z.unknown()
});

export async function adminRoutes(app: FastifyInstance) {
  app.get('/api/admin/users', { preHandler: [requireSuperAdmin] }, async () => {
    return prisma.user.findMany({
      select: { id: true, email: true, role: true, creditsPence: true, appMembership: true }
    });
  });

  app.post('/api/admin/override', { preHandler: [requireSuperAdmin] }, async (req) => {
    const actor = req.user as { userId: string; email: string };
    const input = OverrideInput.parse(req.body);

    const row = await prisma.featureOverride.create({
      data: {
        userId: input.userId,
        appSlug: input.appSlug,
        featureKey: input.featureKey,
        featureValue: input.featureValue as object,
        createdBy: actor.email
      }
    });

    await writeAuditLog({
      actorUserId: actor.userId,
      actorEmail: actor.email,
      action: 'ADMIN_OVERRIDE_FEATURE',
      targetType: 'FeatureOverride',
      targetId: row.id,
      payload: input
    });

    return row;
  });

  app.get('/api/admin/logs', { preHandler: [requireSuperAdmin] }, async () => {
    return prisma.auditLog.findMany({ orderBy: { createdAt: 'desc' }, take: 200 });
  });

  app.get('/api/admin/workforce/suggestions', { preHandler: [requireSuperAdmin] }, async () => {
    return prisma.workforceSuggestion.findMany({ orderBy: { createdAt: 'desc' }, take: 200 });
  });

  app.post('/api/admin/workforce/:id/request-approval', { preHandler: [requireAdminOrSuper] }, async (req, reply) => {
    const actor = req.user as { email: string; userId: string };
    const id = (req.params as { id: string }).id;

    const suggestion = await prisma.workforceSuggestion.findUnique({ where: { id } });
    if (!suggestion) {
      return reply.code(404).send({ error: 'suggestion_not_found' });
    }

    const { signature, timestamp } = generateApprovalSignature(actor.email, id, env.JWT_ACCESS_SECRET);

    const approval = await prisma.adminChangeApproval.create({
      data: {
        suggestionId: id,
        requestedBy: actor.email,
        status: 'PENDING'
      }
    });

    await prisma.workforceSuggestion.update({ where: { id }, data: { status: 'AWAITING_APPROVAL' } });

    await writeAuditLog({
      actorUserId: actor.userId,
      actorEmail: actor.email,
      action: 'WORKFORCE_APPROVAL_REQUESTED',
      targetType: 'WorkforceSuggestion',
      targetId: id,
      payload: { approvalId: approval.id }
    });

    // Return signature for the approver to include in the approval call
    return { ...approval, signature, timestamp };
  });

  app.post('/api/admin/workforce/:id/approve', { preHandler: [requireSuperAdmin] }, async (req, reply) => {
    const actor = req.user as { email: string; userId: string };
    const id = (req.params as { id: string }).id;

    const body = req.body as { requestedByEmail: string; signature: string; timestamp: number };
    if (!body?.signature || !body?.timestamp || !body?.requestedByEmail) {
      return reply.code(400).send({ error: 'missing_signature_fields' });
    }

    const valid = verifyApprovalSignature(
      body.requestedByEmail,
      id,
      body.timestamp,
      body.signature,
      env.JWT_ACCESS_SECRET
    );

    if (!valid) {
      return reply.code(403).send({ error: 'invalid_or_expired_approval_signature' });
    }

    const approval = await prisma.adminChangeApproval.findFirst({
      where: { suggestionId: id, status: 'PENDING' },
      orderBy: { createdAt: 'desc' }
    });

    if (!approval) {
      return reply.code(404).send({ error: 'pending_approval_not_found' });
    }

    await prisma.adminChangeApproval.update({
      where: { id: approval.id },
      data: { status: 'APPROVED', approvedBy: actor.email }
    });

    await prisma.workforceSuggestion.update({ where: { id }, data: { status: 'APPROVED_FOR_EXECUTION' } });
    await workforceQueue.add('open-pr-task', { suggestionId: id });

    await writeAuditLog({
      actorUserId: actor.userId,
      actorEmail: actor.email,
      action: 'WORKFORCE_APPROVED',
      targetType: 'WorkforceSuggestion',
      targetId: id
    });

    return { ok: true, suggestionId: id, queued: true };
  });
}
