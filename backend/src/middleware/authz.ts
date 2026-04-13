import { FastifyReply, FastifyRequest } from 'fastify';
import { env } from '../config.js';

export async function requireAuth(request: FastifyRequest, reply: FastifyReply) {
  await request.jwtVerify();
  return reply;
}

export async function requireSuperAdmin(request: FastifyRequest, reply: FastifyReply) {
  await request.jwtVerify();
  const user = request.user as { email?: string; role?: string };
  if (user.email !== env.SUPER_ADMIN_EMAIL && user.role !== 'SUPER_ADMIN') {
    return reply.code(403).send({ error: 'super_admin_required' });
  }
}

export async function requireAdminOrSuper(request: FastifyRequest, reply: FastifyReply) {
  await request.jwtVerify();
  const user = request.user as { role?: string };
  if (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN') {
    return reply.code(403).send({ error: 'admin_required' });
  }
}
