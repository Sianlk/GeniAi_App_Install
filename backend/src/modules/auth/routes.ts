import { randomBytes, createHash } from 'node:crypto';
import { FastifyInstance } from 'fastify';
import argon2 from 'argon2';
import { z } from 'zod';
import { prisma } from '../../db.js';
import { env } from '../../config.js';

const AuthIn = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const RefreshIn = z.object({ refreshToken: z.string().min(20) });

function hashToken(token: string) {
  return createHash('sha256').update(token).digest('hex');
}

async function issueTokens(
  app: FastifyInstance,
  user: { id: string; email: string; role: string; appMembership: string[] },
) {
  const accessToken = app.jwt.sign(
    {
      userId: user.id,
      email: user.email,
      role: user.role,
      appMembership: user.appMembership,
      tokenVersion: Date.now(),
    },
    { expiresIn: env.JWT_ACCESS_TTL },
  );

  const refreshTokenRaw = randomBytes(48).toString('hex');
  await prisma.refreshToken.create({
    data: {
      userId: user.id,
      tokenHash: hashToken(refreshTokenRaw),
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30),
    },
  });

  return { accessToken, refreshToken: refreshTokenRaw };
}

export async function authRoutes(app: FastifyInstance) {
  app.post('/api/auth/register', async (req, reply) => {
    const input = AuthIn.parse(req.body);
    const role = input.email === env.SUPER_ADMIN_EMAIL ? 'SUPER_ADMIN' : 'USER';
    const passwordHash = await argon2.hash(input.password);

    const user = await prisma.user.upsert({
      where: { email: input.email },
      update: { passwordHash, role, appMembership: role === 'SUPER_ADMIN' ? ['*'] : [] },
      create: {
        email: input.email,
        passwordHash,
        role,
        appMembership: role === 'SUPER_ADMIN' ? ['*'] : [],
      },
    });

    const tokens = await issueTokens(app, user);
    return reply.code(201).send({
      ...tokens,
      user: { id: user.id, email: user.email, role: user.role },
    });
  });

  app.post('/api/auth/token', async (req, reply) => {
    const input = AuthIn.parse(req.body);
    const user = await prisma.user.findUnique({ where: { email: input.email } });

    const valid = user ? await argon2.verify(user.passwordHash, input.password) : false;
    if (!valid || !user) {
      return reply.code(401).send({ error: 'invalid_credentials' });
    }

    const tokens = await issueTokens(app, user);
    return reply.send({
      ...tokens,
      token_type: 'bearer',
      user_id: user.id,
      email: user.email,
      role: user.role,
    });
  });

  app.post('/api/auth/refresh', async (req, reply) => {
    const { refreshToken } = RefreshIn.parse(req.body);
    const refresh = await prisma.refreshToken.findUnique({
      where: { tokenHash: hashToken(refreshToken) },
      include: { user: true },
    });

    if (!refresh || refresh.revokedAt || refresh.expiresAt < new Date()) {
      return reply.code(401).send({ error: 'invalid_refresh_token' });
    }

    await prisma.refreshToken.update({
      where: { id: refresh.id },
      data: { revokedAt: new Date() },
    });

    const tokens = await issueTokens(app, refresh.user);
    return reply.send(tokens);
  });

  app.get('/api/auth/me', { preHandler: [app.authenticate] }, async (req, reply) => {
    const jwtUser = req.user as { userId: string; email: string; role: string };
    return reply.send(jwtUser);
  });
}
