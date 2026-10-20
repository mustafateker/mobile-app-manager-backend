# Mobile App Manager Backend

Mobile App Manager için FastAPI, SQLite ve AsoBeast entegrasyonlu Python API.

Kod, özellik bazlı modüllere ayrılmıştır. Her modülün HTTP katmanı
`controller.py`, doğrulama modelleri `dto.py`, iş mantığı ise `service.py`
dosyasındadır.

## Local development

Python 3.12 veya üzeri gerekir.

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python3 main.py
```

Sonraki çalıştırmalarda proje dizininde sanal ortamı etkinleştirip doğrudan
`python3 main.py` komutunu kullanabilirsiniz. Giriş dosyası `.env` dosyasını
otomatik yükler.

API varsayılan olarak `http://localhost:4100` adresinde çalışır.

## Docker

`.env.example` dosyasını `.env` olarak kopyalayıp güvenli yönetici bilgileri ve
en az 32 karakterlik bir `SESSION_SECRET` tanımlayın. Ardından:

```bash
docker compose up -d --build
```

SQLite verisi Docker volume içinde kalıcı olarak saklanır. AsoBeast erişimi
`ASOBEAST_BASE_URL` ve `ASOBEAST_API_TOKEN` ile yapılandırılır.

## Test

```bash
pytest
```

## Automatic deployment

Every push to `main` runs `.github/workflows/deploy.yml`. The workflow connects
to the production server, pulls the branch with fast-forward protection and
rebuilds the Docker service. Configure `DEPLOY_HOST`, `DEPLOY_USER`,
`DEPLOY_SSH_KEY` and `DEPLOY_KNOWN_HOSTS` as GitHub Actions secrets. Runtime
application credentials remain only in the server-side `.env` file.
