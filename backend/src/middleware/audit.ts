import { prisma } from '../db.js';

export async function writeAuditLog(input: {
  actorUserId: string;
  actorEmail: string;
  action: string;
  targetType: string;
  targetId?: string;
  payload?: unknown;
}) {
  await prisma.auditLog.create({
    data: {
      actorUserId: input.actorUserId,
      actorEmail: input.actorEmail,
      action: input.action,
      targetType: input.targetType,
      targetId: input.targetId,
      payload: input.payload as object | undefined
    }
  });
}
