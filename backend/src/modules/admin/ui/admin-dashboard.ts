import { FastifyInstance } from 'fastify';
import { env } from '../../../config.js';

export async function adminDashboardRoute(app: FastifyInstance) {
  app.get('/admin', { preHandler: [app.authenticate] }, async (req, reply) => {
    const user = req.user as { email: string };
    if (user.email !== env.SUPER_ADMIN_EMAIL) {
      return reply.code(403).send({ error: 'super_admin_required' });
    }

    const html = `<!doctype html>
<html>
<head><title>Hostur Super Admin</title><meta charset="utf-8" /></head>
<body style="font-family: ui-sans-serif; margin: 24px;">
  <h1>Hostur Unified Admin</h1>
  <p>Super admin account: <b>${env.SUPER_ADMIN_EMAIL}</b></p>
  <ul>
    <li><a href="/api/admin/users">Users</a></li>
    <li><a href="/api/admin/logs">Audit logs</a></li>
    <li><a href="/api/admin/workforce/suggestions">AI workforce suggestions</a></li>
  </ul>
</body>
</html>`;
    return reply.type('text/html').send(html);
  });
}
