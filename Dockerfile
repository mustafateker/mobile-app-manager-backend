FROM python:3.13-slim
WORKDIR /app
ENV NODE_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY app app
RUN pip install --no-cache-dir .
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "4100", "--proxy-headers"]
