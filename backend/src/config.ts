import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const Env = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('production'),
  PORT: z.coerce.number().default(8080),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_ACCESS_SECRET: z.string().min(16),
  JWT_REFRESH_SECRET: z.string().min(16),
  JWT_ACCESS_TTL: z.string().default('15m'),
  JWT_REFRESH_TTL: z.string().default('30d'),
  LOGO_URL: z.string().url(),
  SUPER_ADMIN_EMAIL: z.string().email(),
  STRIPE_SECRET_KEY: z.string().min(5),
  STRIPE_WEBHOOK_SECRET: z.string().min(5),
  GITHUB_TOKEN: z.string().optional(),
  GITHUB_OWNER: z.string().default('Sianlk'),
  GITHUB_REPO: z.string().default('GeniAi_App_Install'),
  OPENAI_API_KEY: z.string().optional()
});

export const env = Env.parse(process.env);
