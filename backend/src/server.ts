import { setupTelemetry } from './telemetry.js';
setupTelemetry(); // must be first — instruments http, fastify, redis, pg

import Fastify from 'fastify';
import jwt from '@fastify/jwt';
import websocket from '@fastify/websocket';
import { env } from './config.js';
import { registerSecurity } from './security.js';
import { authRoutes } from './modules/auth/routes.js';
import { adminRoutes } from './modules/admin/routes.js';
import { creditRoutes } from './modules/credits/routes.js';
import { appRoutes } from './modules/apps/routes.js';
import { runSupervisorCycle } from './modules/ai-workforce/supervisor.js';
import { adminDashboardRoute } from './modules/admin/ui/admin-dashboard.js';
import { metricsRoutes } from './modules/metrics/routes.js';
import { syncRoutes } from './modules/apps/sync-routes.js';

declare module 'fastify' {
  interface FastifyInstance {
    authenticate: any;
  }
}

const app = Fastify({ logger: true });

await registerSecurity(app);
await app.register(websocket);

await app.register(jwt, {
  secret: env.JWT_ACCESS_SECRET
});

app.decorate('authenticate', async (request: any, reply: any) => {
  try {
    await request.jwtVerify();
  } catch {
    return reply.code(401).send({ error: 'unauthorized' });
  }
});

app.addHook('onSend', async (_request, reply, payload) => {
  reply.header('X-Platform-Logo', env.LOGO_URL);
  return payload;
});

app.get('/health', async () => ({ ok: true, service: 'unified-backend' }));
app.get('/api/meta/brand', async () => ({ logoUrl: env.LOGO_URL, superAdmin: env.SUPER_ADMIN_EMAIL }));

app.get('/ws/trading', { websocket: true }, async (connection, req) => {
  try {
    const token = (req.query as { token?: string }).token;
    const appSlug = (req.query as { appSlug?: string }).appSlug;
    if (!token || !appSlug) {
      connection.socket.close(1008, 'missing_auth_context');
      return;
    }

    const decoded = await app.jwt.verify<{ appMembership?: string[] }>(token);
    const memberships = decoded.appMembership ?? [];
    if (!(memberships.includes('*') || memberships.includes(appSlug))) {
      connection.socket.close(1008, 'app_access_denied');
      return;
    }
  } catch {
    connection.socket.close(1008, 'invalid_token');
    return;
  }

  const timer = setInterval(() => {
    const payload = {
      symbol: 'BTC-USD',
      confidence: Number((0.7 + Math.random() * 0.29).toFixed(3)),
      action: ['BUY', 'SELL', 'HOLD'][Math.floor(Math.random() * 3)]
    };
    connection.socket.send(JSON.stringify(payload));
  }, 1200);

  connection.socket.on('close', () => clearInterval(timer));
});

await authRoutes(app);
await adminRoutes(app);
await adminDashboardRoute(app);
await creditRoutes(app);
await appRoutes(app);
await syncRoutes(app);
await metricsRoutes(app);

app.post('/api/workforce/run', { preHandler: [app.authenticate] }, async (req, reply) => {
  const user = req.user as { email: string };
  if (user.email !== env.SUPER_ADMIN_EMAIL) {
    return reply.code(403).send({ error: 'super_admin_required' });
  }

  const res = await runSupervisorCycle();
  return reply.send(res);
});

app.listen({ host: '0.0.0.0', port: env.PORT });
