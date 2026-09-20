# Deployment configuration: Lightning now, AWS later

One backend and one frontend are used on every host. Provider choice is an
explicit operational declaration, not automatic proof of cloud identity. No
provider SDK, credentials, public hostname or Studio folder is embedded in model
or API code. The hosted command guard checks Linux and the known Studio/Colab
workspace only to prevent accidental execution on the development PC.

## Backend settings

Copy root `.env.example` to root `.env` on the cloud host (the setup command does
this if missing). The common launcher selects it by absolute path, regardless
of the current terminal directory. Use `--env-file /absolute/path/custom.env`
to choose another file. Direct Python/Uvicorn commands can set `APP_ENV_FILE`.
Process environment variables override the selected file. Docker Compose reads
the root `.env` and supplies its values as container environment variables.

| Setting | Lightning native | AWS full Docker Compose |
|---|---|---|
| `EXECUTION_TARGET` | `lightning` | `aws` |
| `ENABLE_MODEL_INFERENCE` | `true` after setup | `true` after GPU checks |
| `MODEL_ID` / `MODEL_REVISION` | Pinned Qwen values from example | Same values |
| `MODEL_DTYPE` | `auto` (selected from PyTorch CUDA capability checks) | Same |
| `MODEL_CACHE_DIR` | Omit for HF default, or absolute persistent Studio path | Omit to use `HF_HOME=/opt/model-cache` volume |
| `BACKEND_HOST` / `BACKEND_PORT` | `0.0.0.0` / `8000`, configurable | Same internal defaults |
| `CORS_ORIGINS` | Exact frontend origins for direct browser requests | `[]` for same-origin Nginx |
| `ENABLE_API_DOCS` | Optional `true` for browser testing | Normally `false` |
| Frontend `API_BASE_URL` | Public backend origin for direct browser mode | Empty |
| Frontend `API_PROXY_URL` | Public backend origin for proxy mode | `http://backend:8000` |

Inference is disabled in committed examples and application defaults. An explicit
cloud target and opt-in are both required before model imports/downloads. CUDA
remains required. No CPU fallback, alternative vendor or production mock exists.

If moving an existing `.env` from Lightning to AWS, remove Studio-only absolute
paths and any `APP_ENV_FILE` or `HF_HOME` set for that machine. Use the mounted
container cache instead. If changing the backend port in Compose, also change
`API_PROXY_URL` to the same internal port. Keep the container host `0.0.0.0` so
Nginx can reach it; the backend has no public host port in full Compose.

The shared launcher supports `setup`, `test`, `serve`, and `smoke` with
`--cloud-target aws|lightning|colab`. Run them only on the selected hosted Linux
runtime. `setup` and `test` explicitly disable inference in their subprocesses;
`serve` respects the configured target and opt-in. One worker is intentional:
each additional worker would duplicate GPU weights and split in-memory jobs.

## Frontend option A: direct calls from a static host

The browser reads `/app-config.json` with cache disabled and caches the parsed
origin for that page session. Empty `apiBaseUrl` means same-origin `/api` calls.
To connect a separately hosted frontend, deploy this small configuration file:

```json
{"apiBaseUrl":"https://YOUR-LIGHTNING-BACKEND-ORIGIN"}
```

Use only an HTTP(S) origin, without credentials, an `/api` suffix, query or
fragment. An HTTPS frontend requires an HTTPS backend. Configure the static
host's CSP `connect-src` to allow that exact backend origin. Configure FastAPI's
`CORS_ORIGINS` with the exact frontend origin. CORS does not authenticate users.

For a frontend built on an authorized hosted environment, generate the runtime
file after building, from `frontend/`:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm run build
API_BASE_URL=https://YOUR-LIGHTNING-BACKEND-ORIGIN node scripts/configure-runtime.mjs dist
```

Upload `dist/` to the chosen static host. Configure `app-config.json` with
`Cache-Control: no-store` or revalidation. Change only that deployed JSON and
refresh open pages when the backend URL changes; the React bundle need not be
rebuilt. Do not place secrets in it. Do not run these build commands locally.

## Frontend option B: AWS Nginx proxies to Lightning

On the AWS frontend host, configure root `.env`:

```dotenv
EXECUTION_TARGET=disabled
ENABLE_MODEL_INFERENCE=false
API_BASE_URL=
API_PROXY_URL=https://YOUR-LIGHTNING-BACKEND-ORIGIN
HTTP_BIND=127.0.0.1
HTTP_PORT=8080
```

Then, on AWS only:

```bash
docker compose -f compose.frontend.yml up -d --build
curl -fsS http://127.0.0.1:8080/api/ready
```

Only the frontend container starts. Its Nginx serves React and proxies `/api/`
to Lightning, including HTTPS SNI and certificate verification. The browser
uses one origin, so CORS can stay empty. Follow the AWS HTTPS/public-access
guide to expose this loopback service. A frontend-only host needs enough memory
for the build; serving static output uses less memory than building it.

Alternatively set `API_BASE_URL` to Lightning for direct browser mode in the
container; its startup script writes the runtime JSON and CSP. In this mode
the proxy fallback is set to the same external origin, so no sibling backend
container is required. Browser mode needs backend CORS. Origin values for this
container must use DNS names/IPv4 with optional port, no trailing slash.

When a deployment variable changes, recreate the container with
`docker compose -f compose.frontend.yml up -d --force-recreate`; `restart` alone
does not refresh Compose environment values. Reload browser pages afterward.

## Move the whole application to AWS

Use the same repository and [AWS deployment guide](aws-deployment.md). Starting
from the root example, enable AWS inference, leave `API_BASE_URL` empty and set
`API_PROXY_URL=http://backend:8000`. Then use full `docker-compose.yml` on the
GPU server. Stop a frontend-only deployment before replacing it on the same
host port. No source edits or cloud-specific model patches are needed.

## Hosted acceptance

- Dependency consistency, CUDA visibility and all non-model tests pass.
- Readiness becomes true with the pinned real Qwen checkpoint.
- Real smoke checks pass; manually inspect cards and workbook.
- At the deployed frontend origin, test upload, job polling, edit, export and
  delete. Check browser Network/Console for CORS, CSP and mixed-content failures.
- Confirm rejected origins fail CORS preflight in direct mode.
- Switch backend URL through deployment configuration and confirm the unchanged
  frontend bundle uses the new URL after reload/recreation.
- Record memory, startup time, cache reuse, public access and actual cost.

These checks are authored but unexecuted for this revision. Source inspection
does not establish runtime acceptance. Complete AWS Docker/public acceptance
on AWS even if native Lightning testing passes.
