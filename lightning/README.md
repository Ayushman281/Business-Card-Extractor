# Deploy the Full Application on Lightning AI

This guide runs both the pretrained Qwen backend and the React frontend in one
Lightning AI Studio. The backend and frontend use separate HTTPS Port Viewer
origins and communicate through an explicit CORS allowlist.

Current user-operated deployment:

- Frontend: <https://5173-01m2w98emjfcmws3qnw3cmh05x.cloudspaces.litng.ai>
- Backend readiness: <https://8000-01m2w98emjfcmws3qnw3cmh05x.cloudspaces.litng.ai/api/ready>
- Backend API documentation: <https://8000-01m2w98emjfcmws3qnw3cmh05x.cloudspaces.litng.ai/docs>

These addresses work only while the Studio and application processes remain
available. New Studios receive different addresses.

## Requirements

- A fresh Lightning AI Studio with an NVIDIA GPU. A T4 with 16 GB VRAM is the
  intended minimum for this configuration.
- Python 3.11–3.13.
- Node.js 22.12 or newer.
- At least 30 GiB free disk for packages and model weights.
- The current source repository or `business-card-lead-extractor-final.zip`.

No training or fine-tuning is performed. Backend startup downloads the official
pretrained checkpoint only after inference is explicitly enabled on the hosted GPU.

## 1. Upload and enter the project

Upload the ZIP using the Studio file explorer, then run:

```bash
cd /teamspace/studios/this_studio
unzip business-card-lead-extractor-final.zip
cd business-card-lead-extractor

python --version
node --version
nvidia-smi
```

If the ZIP was already extracted, run only the `cd` and verification commands.
If Node is older and the Studio provides `nvm`, select Node 22:

```bash
nvm install 22
nvm use 22
```

## 2. Install backend dependencies and run non-model checks

From the repository root:

```bash
python scripts/cloud_backend.py setup --cloud-target lightning --run-tests
```

The command installs the pinned CUDA/Python dependencies in the fresh Studio
environment, checks dependency consistency and GPU access, and runs the non-model
test suite. It creates `.env` with inference disabled. It does not load Qwen.

Stop if setup fails. Diagnostic files are written under `.runtime/reports/`,
including `pip-check.txt`, `gpu-check.txt`, package versions, and pytest output.

## 3. Configure the backend

Open the root `.env` in the Studio editor or run:

```bash
sed -i \
  -e 's/^EXECUTION_TARGET=.*/EXECUTION_TARGET=lightning/' \
  -e 's/^ENABLE_MODEL_INFERENCE=.*/ENABLE_MODEL_INFERENCE=true/' \
  -e 's/^MODEL_DTYPE=.*/MODEL_DTYPE=auto/' \
  -e 's/^BACKEND_HOST=.*/BACKEND_HOST=0.0.0.0/' \
  -e 's/^BACKEND_PORT=.*/BACKEND_PORT=8000/' \
  -e 's/^ENABLE_API_DOCS=.*/ENABLE_API_DOCS=true/' \
  .env
```

Keep the pinned `MODEL_ID` and `MODEL_REVISION`. `MODEL_DTYPE=auto` chooses a
supported GPU dtype. The model cache uses the persistent Studio environment by
default. An optional `MODEL_CACHE_DIR` must be an absolute hosted path.

Verify the settings:

```bash
grep -E '^(EXECUTION_TARGET|ENABLE_MODEL_INFERENCE|MODEL_ID|MODEL_DTYPE|BACKEND_HOST|BACKEND_PORT|CORS_ORIGINS|ENABLE_API_DOCS)=' .env
```

Do not paste Markdown link syntax into `.env`. A CORS value must look exactly
like `CORS_ORIGINS=["https://frontend-origin"]`.

## 4. Start the backend

Use Terminal 1:

```bash
cd /teamspace/studios/this_studio/business-card-lead-extractor
python scripts/cloud_backend.py serve --cloud-target lightning
```

Leave this terminal running. The first start downloads about 7.5 GB of model
shards and initializes Qwen. A message such as the following indicates success:

```text
model_initialized startup_seconds=...
```

The terminal then remains occupied because it is serving requests. Access logs
are disabled, so an idle server is normally quiet.

From Terminal 2:

```bash
curl -sS http://127.0.0.1:8000/api/health
curl -sS http://127.0.0.1:8000/api/ready
```

Readiness must return:

```json
{"ready":true}
```

An HTTP 503 while the model is loading is expected. A `failed` model state needs
investigation in Terminal 1.

## 5. Expose the backend

Open Lightning's **Port Viewer** plugin:

1. Select **New Port**.
2. Enter port `8000` and name it `backend` or `port-8000`.
3. Enable the public URL option.
4. Open the port entry in a new tab and copy the origin from the address bar.

Confirm these paths in a browser:

```text
https://YOUR-BACKEND-ORIGIN/api/ready
https://YOUR-BACKEND-ORIGIN/docs
```

Use only the origin when configuring React—do not append `/api`, `/ready`,
`/docs`, or a trailing slash. The endpoint must be accessible without a Lightning
login redirect for a separately hosted browser frontend to call it.

## 6. Build and start the frontend

Use Terminal 2:

```bash
cd /teamspace/studios/this_studio/business-card-lead-extractor/frontend
npm ci --ignore-scripts --no-audit --no-fund
npm run build
```

Write the backend's public origin into the runtime file. Substitute the URL
created in the previous step:

```bash
CARD_BACKEND_ORIGIN="https://YOUR-BACKEND-ORIGIN"
API_BASE_URL="$CARD_BACKEND_ORIGIN" node scripts/configure-runtime.mjs dist
cat dist/app-config.json
```

Start the static frontend server:

```bash
python -m http.server 5173 --bind 0.0.0.0 --directory dist
```

Leave Terminal 2 running. Add port `5173` in Port Viewer, make it public, and
copy its origin.

## 7. Allow the frontend origin and restart the backend

Use Terminal 3. Substitute the exact port-5173 origin, without a trailing slash:

```bash
cd /teamspace/studios/this_studio/business-card-lead-extractor
CARD_FRONTEND_ORIGIN="https://YOUR-FRONTEND-ORIGIN"
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=[\"${CARD_FRONTEND_ORIGIN}\"]|" .env
grep '^CORS_ORIGINS=' .env
```

Expected format:

```dotenv
CORS_ORIGINS=["https://YOUR-FRONTEND-ORIGIN"]
```

Return to Terminal 1, press `Ctrl+C`, and restart the backend:

```bash
python scripts/cloud_backend.py serve --cloud-target lightning
```

Wait for readiness, then refresh the frontend URL. The status should change to
**Qwen is ready**. Upload fictional card images, review the results, edit a field,
and download the Excel workbook.

## 8. Run hosted smoke checks

With the backend running, use Terminal 3:

```bash
cd /teamspace/studios/this_studio/business-card-lead-extractor
python scripts/cloud_backend.py smoke --cloud-target lightning
```

If the sample generator reports a missing font:

```bash
sudo apt-get update
sudo apt-get install -y fonts-dejavu-core
python scripts/cloud_backend.py smoke --cloud-target lightning
```

To exercise the public backend route too:

```bash
python scripts/cloud_backend.py smoke \
  --cloud-target lightning \
  --base-url "https://YOUR-BACKEND-ORIGIN"
```

Review `.runtime/reports/smoke-report.json` and open
`.runtime/reports/smoke-report.xlsx`. The check submits fictional images to the
already-running model; it does not load a second model.

## Start the application again later

Dependencies, source, and model cache normally persist with the Studio. After
starting the GPU machine again, open two terminals.

Terminal 1:

```bash
cd /teamspace/studios/this_studio/business-card-lead-extractor
python scripts/cloud_backend.py serve --cloud-target lightning
```

Terminal 2:

```bash
cd /teamspace/studios/this_studio/business-card-lead-extractor/frontend
python -m http.server 5173 --bind 0.0.0.0 --directory dist
```

Check whether Lightning retained or regenerated the two public port URLs. If an
origin changes, regenerate `frontend/dist/app-config.json`, update
`CORS_ORIGINS`, and restart the backend.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| Port Viewer says nothing is running | Confirm the terminal command is still active; run `ss -ltnp \| grep ':8000'` and local `curl` before recreating the port entry. |
| `Connection refused` on port 8000 | Start the backend and leave Terminal 1 open. |
| Backend exits during settings load | Check `.env`, especially the JSON syntax of `CORS_ORIGINS`. |
| `Address already in use` | Do not start another model; inspect the existing listener with `ss -ltnp \| grep ':8000'`. |
| UI remains on “Connecting to server” | Verify `dist/app-config.json`, public backend access, exact CORS origin, HTTPS, and browser Console/Network errors. |
| Browser reports a CORS error | Update `CORS_ORIGINS` to the exact frontend origin and restart the backend. |
| Model remains loading | Inspect Terminal 1, free disk, network access, and `nvidia-smi`; avoid repeated restarts during download. |
| CUDA out of memory | Ensure only one backend/model process is running and no notebook holds the GPU. |
| Port URL opens a login page | Change the port visibility/access setting; cross-origin browser calls require a reachable endpoint. |

## Shutdown and cost control

Press `Ctrl+C` in both server terminals. Stop the GPU Studio when the demo ends;
closing a browser tab alone does not necessarily stop GPU use. Check the current
credits and pricing displayed in the Lightning account. Public Studio links are
appropriate for an assessment/demo, not permanent production availability.

The same application can later move to AWS without source changes. Follow
[the AWS guide](../aws/README.md) and switch the environment target to `aws`.
