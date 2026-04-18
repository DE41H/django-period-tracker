FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv pip install --system --no-dev .

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
