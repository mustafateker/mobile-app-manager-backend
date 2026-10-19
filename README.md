# Mobile App Manager Backend

Mobile App Manager için Fastify, SQLite ve AsoBeast entegrasyonlu API.

## Local development

Node.js 24 ve pnpm 12 gerekir.

```bash
cp .env.example .env
corepack pnpm install
corepack pnpm dev
```

API varsayılan olarak `http://localhost:4100` adresinde çalışır.

## Docker

`.env.example` dosyasını `.env` olarak kopyalayıp güvenli yönetici bilgileri ve
en az 32 karakterlik bir `SESSION_SECRET` tanımlayın. Ardından:

```bash
docker compose up -d --build
```

SQLite verisi Docker volume içinde kalıcı olarak saklanır. AsoBeast erişimi
`ASOBEAST_BASE_URL` ve `ASOBEAST_API_TOKEN` ile yapılandırılır.

## Automatic deployment

Every push to `main` runs `.github/workflows/deploy.yml`. The workflow connects
to the production server, pulls the branch with fast-forward protection and
rebuilds the Docker service. Configure `DEPLOY_HOST`, `DEPLOY_USER`,
`DEPLOY_SSH_KEY` and `DEPLOY_KNOWN_HOSTS` as GitHub Actions secrets. Runtime
application credentials remain only in the server-side `.env` file.
