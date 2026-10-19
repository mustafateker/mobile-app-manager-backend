import { z } from 'zod';

const schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().positive().default(4100),
  DATABASE_PATH: z.string().default('./data/manager.sqlite'),
  ADMIN_EMAIL: z.string().email().default('admin@triworkster.com'),
  ADMIN_PASSWORD: z.string().min(10),
  SESSION_SECRET: z.string().min(32),
  WEB_ORIGIN: z.string().url().default('http://localhost:5173'),
  ASOBEAST_BASE_URL: z.string().url().default('http://127.0.0.1:3001/api/backend'),
  ASOBEAST_API_TOKEN: z.string().optional().default(''),
});

export type Config = z.infer<typeof schema>;
export const readConfig = (env: NodeJS.ProcessEnv = process.env): Config => schema.parse(env);
