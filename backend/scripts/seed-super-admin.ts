import { env } from '../src/config.js';
import { prisma } from '../src/db.js';
import argon2 from 'argon2';

const passwordHash = await argon2.hash('change_me_now');

await prisma.user.upsert({
  where: { email: env.SUPER_ADMIN_EMAIL },
  update: { role: 'SUPER_ADMIN', passwordHash },
  create: {
    email: env.SUPER_ADMIN_EMAIL,
    passwordHash,
    role: 'SUPER_ADMIN',
    appMembership: ['*']
  }
});

console.log(`super admin ensured: ${env.SUPER_ADMIN_EMAIL}`);
await prisma.$disconnect();
