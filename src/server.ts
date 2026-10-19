import Fastify from 'fastify';
import cookie from '@fastify/cookie';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import { z } from 'zod';
import { readConfig, type Config } from './config.js';
import { AppDatabase } from './database.js';
import { AsoBeastClient } from './asobeast.js';
import { clearSession, isAuthenticated, passwordMatches, setSession } from './auth.js';

const nullableUrl = z.union([z.string().url(), z.literal(''), z.null()]).transform((v) => v || null);
const nullableText = z.union([z.string().max(200), z.literal(''), z.null()]).transform((v) => v || null);
const appInput = z.object({
  name: z.string().trim().min(2).max(80),
  slug: z.string().trim().regex(/^[a-z0-9-]+$/),
  iosBundleId: nullableText,
  androidPackage: nullableText,
  appStoreUrl: nullableUrl,
  playStoreUrl: nullableUrl,
  asoBeastAppId: nullableText,
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/).default('#2563eb'),
  status: z.enum(['development', 'review', 'live']).default('development'),
});

export async function buildServer(config: Config) {
  const app = Fastify({ logger: config.NODE_ENV !== 'test', trustProxy: true });
  const db = new AppDatabase(config.DATABASE_PATH);
  const aso = new AsoBeastClient(config.ASOBEAST_BASE_URL, config.ASOBEAST_API_TOKEN);
  const secure = config.NODE_ENV === 'production';

  await app.register(helmet);
  await app.register(cookie, { secret: config.SESSION_SECRET, hook: 'onRequest' });
  await app.register(cors, {
    origin: config.WEB_ORIGIN,
    credentials: true,
    methods: ['GET', 'HEAD', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  });
  await app.register(rateLimit, { max: 120, timeWindow: '1 minute' });

  app.get('/health', async () => ({ status: 'ok', asobeastConfigured: aso.configured() }));
  app.post('/v1/auth/login', { config: { rateLimit: { max: 8, timeWindow: '15 minutes' } } }, async (request, reply) => {
    const input = z.object({ email: z.string().email(), password: z.string().min(1) }).parse(request.body);
    if (input.email.toLowerCase() !== config.ADMIN_EMAIL.toLowerCase() || !passwordMatches(input.password, config.ADMIN_PASSWORD)) {
      return reply.code(401).send({ message: 'E-posta veya şifre hatalı.' });
    }
    setSession(reply, secure);
    return { user: { email: config.ADMIN_EMAIL } };
  });
  app.post('/v1/auth/logout', async (_request, reply) => { clearSession(reply, secure); return reply.code(204).send(); });

  app.addHook('preHandler', async (request, reply) => {
    if (request.url.startsWith('/v1/') && !request.url.startsWith('/v1/auth/login') && !isAuthenticated(request)) {
      return reply.code(401).send({ message: 'Oturum gerekli.' });
    }
  });

  app.get('/v1/auth/session', async () => ({ user: { email: config.ADMIN_EMAIL } }));
  app.get('/v1/apps', async () => db.list());
  app.post('/v1/apps', async (request, reply) => reply.code(201).send(db.create(appInput.parse(request.body))));
  app.patch('/v1/apps/:id', async (request, reply) => {
    const { id } = z.object({ id: z.string().uuid() }).parse(request.params);
    const parsed = appInput.partial().parse(request.body);
    const changes = Object.fromEntries(Object.entries(parsed).filter(([, value]) => value !== undefined));
    const result = db.update(id, changes);
    return result ?? reply.code(404).send({ message: 'Uygulama bulunamadı.' });
  });

  app.get('/v1/dashboard', async () => {
    const apps = db.list();
    let remoteApps: Array<Record<string, unknown>> = [];
    let connected = false;
    if (aso.configured()) {
      try { remoteApps = await aso.apps(); connected = true; } catch { connected = false; }
    }
    return { apps, asobeast: { configured: aso.configured(), connected, remoteAppCount: remoteApps.length } };
  });
  app.get('/v1/aso/status', async () => {
    if (!aso.configured()) return { configured: false, connected: false };
    try { return { configured: true, connected: true, details: await aso.status() }; }
    catch (error) { return { configured: true, connected: false, error: error instanceof Error ? error.message : 'Bağlantı hatası' }; }
  });
  app.get('/v1/apps/:id/aso', async (request, reply) => {
    const { id } = z.object({ id: z.string().uuid() }).parse(request.params);
    const managed = db.find(id);
    if (!managed) return reply.code(404).send({ message: 'Uygulama bulunamadı.' });
    if (!managed.asoBeastAppId) return { linked: false };
    const [summary, audit, keywords] = await Promise.all([
      aso.summary(managed.asoBeastAppId), aso.audit(managed.asoBeastAppId), aso.keywords(managed.asoBeastAppId),
    ]);
    return { linked: true, summary, audit, keywords };
  });
  app.post('/v1/apps/:id/aso/import', async (request, reply) => {
    const { id } = z.object({ id: z.string().uuid() }).parse(request.params);
    const managed = db.find(id);
    if (!managed) return reply.code(404).send({ message: 'Uygulama bulunamadı.' });
    const url = managed.appStoreUrl ?? managed.playStoreUrl;
    if (!url) return reply.code(422).send({ message: 'Önce en az bir mağaza bağlantısı ekleyin.' });
    const imported = await aso.import(url);
    const remoteId = typeof imported.id === 'string' ? imported.id : null;
    if (remoteId) db.update(id, { asoBeastAppId: remoteId });
    return { imported, app: db.find(id) };
  });
  app.post('/v1/apps/:id/aso/run', async (request, reply) => {
    const { id } = z.object({ id: z.string().uuid() }).parse(request.params);
    const managed = db.find(id);
    if (!managed?.asoBeastAppId) return reply.code(422).send({ message: 'Uygulama AsoBeast ile bağlı değil.' });
    return aso.runDaily(managed.asoBeastAppId);
  });

  app.setErrorHandler((unknownError, _request, reply) => {
    const error = unknownError instanceof Error ? unknownError : new Error('UNKNOWN_ERROR');
    if (error instanceof z.ZodError) return reply.code(400).send({ message: 'Gönderilen alanları kontrol edin.', issues: error.issues });
    if (error.message === 'ASOBEAST_NOT_CONFIGURED') return reply.code(503).send({ message: 'AsoBeast API token henüz tanımlanmadı.' });
    if (error.message.startsWith('ASOBEAST_')) {
      const match = /^ASOBEAST_(\d+):(.*)$/s.exec(error.message);
      let message = 'AsoBeast isteği başarısız oldu.';
      if (match?.[2]) {
        try {
          const upstream = JSON.parse(match[2]) as { message?: unknown };
          if (typeof upstream.message === 'string') message = upstream.message;
        } catch { /* The upstream body was not JSON. */ }
      }
      const upstreamStatus = Number(match?.[1] ?? 500);
      return reply.code(upstreamStatus >= 400 && upstreamStatus < 500 ? 422 : 502).send({ message });
    }
    const statusCode = 'statusCode' in error && typeof error.statusCode === 'number' ? error.statusCode : 500;
    if (statusCode >= 400 && statusCode < 500) return reply.code(statusCode).send({ message: error.message });
    app.log.error(error);
    return reply.code(500).send({ message: 'Beklenmeyen sunucu hatası.' });
  });
  return app;
}

if (process.env.NODE_ENV !== 'test') {
  const config = readConfig();
  const server = await buildServer(config);
  await server.listen({ host: '0.0.0.0', port: config.PORT });
}
