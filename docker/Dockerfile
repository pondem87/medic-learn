FROM python:3.12.14-slim-bookworm AS build
RUN pip install --no-cache-dir uv==0.12.21
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY config ./config
COPY medic_learn ./medic_learn
COPY templates ./templates
COPY static ./static
COPY scripts ./scripts
COPY manage.py ./
RUN .venv/bin/python manage.py collectstatic --noinput --settings=config.settings.build
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && mkdir -p docker \
    && curl --fail --silent --show-error --connect-timeout 10 --max-time 60 --retry 2 https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o docker/rds-ca.pem \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.12.14-slim-bookworm AS runtime
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DJANGO_SETTINGS_MODULE=config.settings.production
WORKDIR /app
COPY --from=build /app /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --no-create-home app
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
