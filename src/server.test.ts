import { afterEach, describe, expect, it } from 'vitest';
import { unlinkSync } from 'node:fs';
import { buildServer } from './server.js';
import type { Config } from './config.js';

const paths: string[] = [];
const config = (): Config => {
  const path = `/tmp/mobil-app-manager-${crypto.randomUUID()}.sqlite`;
  paths.push(path);
  return { NODE_ENV: 'test', PORT: 4100, DATABASE_PATH: path, ADMIN_EMAIL: 'admin@example.com',
    ADMIN_PASSWORD: 'correct-password', SESSION_SECRET: 'a'.repeat(32), WEB_ORIGIN: 'http://localhost:5173',
    ASOBEAST_BASE_URL: 'http://localhost:3001/api/backend', ASOBEAST_API_TOKEN: '' };
};
afterEach(() => { for (const path of paths.splice(0)) { try { unlinkSync(path); } catch {} } });

describe('api', () => {
  it('protects application data', async () => {
    const app = await buildServer(config());
    const response = await app.inject({ method: 'GET', url: '/v1/apps' });
    expect(response.statusCode).toBe(401);
    await app.close();
  });

  it('logs in and returns seeded apps', async () => {
    const app = await buildServer(config());
    const login = await app.inject({ method: 'POST', url: '/v1/auth/login', payload: { email: 'admin@example.com', password: 'correct-password' } });
    expect(login.statusCode).toBe(200);
    const cookie = login.cookies[0]?.value;
    const apps = await app.inject({ method: 'GET', url: '/v1/apps', cookies: { mam_session: cookie ?? '' } });
    expect(apps.json()).toHaveLength(2);
    await app.close();
  });

  it('returns 400 for malformed json instead of hiding it as a server error', async () => {
    const app = await buildServer(config());
    const response = await app.inject({
      method: 'POST', url: '/v1/auth/login',
      headers: { 'content-type': 'application/json' }, payload: '{invalid',
    });
    expect(response.statusCode).toBe(400);
    await app.close();
  });

  it('allows browser preflight requests for application updates', async () => {
    const app = await buildServer(config());
    const response = await app.inject({
      method: 'OPTIONS',
      url: `/v1/apps/${crypto.randomUUID()}`,
      headers: {
        origin: 'http://localhost:5173',
        'access-control-request-method': 'PATCH',
        'access-control-request-headers': 'content-type',
      },
    });

    expect(response.statusCode).toBe(204);
    expect(response.headers['access-control-allow-methods']).toContain('PATCH');
    expect(response.headers['access-control-allow-headers']?.toLowerCase()).toContain('content-type');
    expect(response.headers['access-control-allow-credentials']).toBe('true');
    await app.close();
  });
});
