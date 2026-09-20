# Build this image on AWS only. Builds do not download model weights.
FROM python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS tests
COPY backend/requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY backend/ .
ENV EXECUTION_TARGET=disabled ENABLE_MODEL_INFERENCE=false
USER app
CMD ["pytest", "-p", "no:cacheprovider"]

FROM base AS runtime
COPY backend/requirements-model.txt backend/requirements-gpu.txt ./
RUN pip install --no-cache-dir -r requirements-gpu.txt --index-url https://download.pytorch.org/whl/cu126 \
    && pip install --no-cache-dir -r requirements-model.txt \
    && mkdir -p /opt/model-cache && chown app:app /opt/model-cache
COPY --chown=app:app backend/app ./app
COPY --chown=app:app backend/scripts ./scripts
ENV HF_HOME=/opt/model-cache HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false
USER app
EXPOSE 8000
CMD ["python", "-m", "app.serve"]
