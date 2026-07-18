FROM node:20-slim AS tailwind-builder
WORKDIR /app
COPY . .
RUN cd theme/static_src && npm install && npm run build


FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .
COPY --from=tailwind-builder /app/theme/static/css/dist ./theme/static/css/dist

RUN DJANGO_SETTINGS_MODULE=config.settings.prod SECRET_KEY=build-only python manage.py collectstatic --no-input

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
