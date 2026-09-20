# Architecture and technical decisions

## Execution boundary

Source is authored on Windows, where only frontend preview is permitted.
Backend tests and pretrained inference run on the explicitly selected hosted
AWS, Lightning AI or Colab GPU runtime. The Docker deployment path targets AWS.
No training/fine-tuning or local CPU/GPU fallback is configured.

`EXECUTION_TARGET=aws|lightning|colab` and `ENABLE_MODEL_INFERENCE=true` are both
required before model imports or weights load. Defaults remain disabled; the
target flag is not cloud identity verification. The shared launcher reads the
root environment file, permits a custom file, and does not patch source or
override configured model/dtype/cache choices. Process environment has priority.

## Deployment topology

Lightning runs the same backend natively with one GPU worker. React can use its
public HTTPS API with exact CORS origins, or Nginx can proxy to it. The frontend
reads an `app-config.json` origin at runtime; changing hosts does not require a
React rebuild. Nginx generates this file and its CSP from deployment environment
settings. Same-origin remains the default. See [portable deployment](portable-deployment.md).

One EC2 host runs two Compose services:

- `frontend`: Nginx serves the Vite output and proxies `/api/`.
- `backend`: one Uvicorn process with FastAPI and one Qwen instance on CUDA.

The backend is reachable only on the Compose network. A Docker named volume
stores Hugging Face weights across restarts. No database is required.

In the initial AWS configuration, the frontend binds to loopback port 8080.
Public HTTP uses an explicit bind change; HTTPS can use a host Nginx/Certbot
proxy to the loopback container without exposing port 8000.

## Model comparison

These are engineering planning estimates, not measurements from this project.

| Checkpoint | Use in this project | Memory/compatibility considerations |
|---|---|---|
| Qwen2.5-VL-3B-Instruct | Preferred pretrained AWS model | Roughly 6–8 GB of FP16 weights, plus vision activations, KV cache, CUDA workspace and host RAM. Plan for a 16 GiB GPU and measure. |
| Qwen2.5-VL-3B-Instruct-AWQ | Evaluated in planning, not implemented | 4-bit weights reduce weight memory, but vision/runtime overhead remains. It would require a compatible quantization backend and compatibility testing before adoption. |
| Qwen2-VL-2B-Instruct | Explicit supported AWS alternative | Smaller weights do not guarantee acceptable CPU latency or fit in a 4 GiB GPU. A different checkpoint class and revision are selected explicitly. |

The native processor receives a Pillow image directly, so qwen-vl-utils/video
dependencies are unnecessary for this image-only path. The installed
torchvision version is paired with PyTorch for vision integration.

The default model uses its research license. See the model license linked in
README. Do not infer model licensing from the application's MIT license.

## Lifecycle

FastAPI lifespan creates the job store and starts a background loader once.
The loader moves from `loading` to `ready` or `failed`; exceptions are logged
server-side. The API remains reachable so the UI can explain model startup.

Health is liveness; readiness is model availability. The Compose healthcheck
uses liveness to avoid repeated restarts during a slow first download. A model
load failure requires investigation and a deliberate restart.

Use exactly one Uvicorn worker. Worker count is not an inference concurrency
control: each worker would independently load several gigabytes of weights
and have a different in-memory job store.

## Batch admission and progress

The extraction route acquires one process-wide asyncio admission lock before
parsing multipart data. A competing upload receives 429 and Retry-After.
Accepted images are transferred to an in-memory job and HTTP 202 returns a
random UUID capability. The browser polls every 1.5 seconds.

The worker passes one card at a time to a synchronous service via
`asyncio.to_thread`. This keeps the API event loop available for progress and
health. A model-level threading lock also serializes generation. The admission
lock remains held for the full batch; there is no unbounded waiting queue.

Per-card validation/model/parser failures produce independent result entries.
Job completion counts processing outcomes, not extraction accuracy.
A valid all-null result is a success with a review warning.

Generation has a cooperative time limit. It cannot forcibly interrupt a GPU
kernel; forcibly cancelling a Python await would not stop that inference.
Shutdown allows in-flight work to finish where possible; Docker eventually
terminates after its grace period. In-memory jobs are then lost.

## Validation and output

- Limits: 20 files, 10 MiB per file, 210 MiB full request, 25 million decoded pixels.
- Export JSON has a separate 1 MiB request-body cap.
- Extension allowlist plus Pillow format check; client MIME is not trusted.
- Animated images are rejected.
- EXIF rotation is applied. Transparent pixels are composited over white.
- The longest side is bounded to 1800 px, then the processor limits visual
  pixels to 1,003,520 (approximately 1280 visual tokens at 28 × 28).
- A deterministic instruction prompt asks for exactly seven nullable fields
  and tells the model to treat image text as data.
- The parser accepts JSON or a recoverable embedded object. It never uses eval
  or fabricates repaired values. Pydantic rejects unknown keys and non-strings.
- Email/phone anomalies produce warnings while preserving source text for review.
- Every Excel value is explicitly stored as a string. Headers are bold, the
  first row is frozen, filters are enabled and widths are bounded.

Changes to upper upload limits also require reviewing Nginx, tmpfs and host RAM.
Both full-request and file limits are needed: multipart boundaries have overhead,
and extension checks alone do not establish what a file actually contains.

## Data lifetime and privacy

Multipart spill files are temporary on a container tmpfs, not an EBS upload
directory. File handles close after request parsing. Raw image bytes are dropped
after each card. Completed leads are retained for 15 minutes at most, and only
32 completed batches are retained; older batches may be evicted earlier.
A background cleanup loop runs every 30 seconds, and lookups also purge expiry.

An unguessable job ID protects against enumeration, not against an authorized
recipient sharing it. No user account or database is present. Do not log IDs,
card contents or raw model responses. Application access logs are disabled.
HTTP responses use no-store. React escapes displayed text and never injects
extracted HTML. The export payload contains the user's corrected values.

Browser previews use object URLs and revoke them on removal/unmount. Leads,
files and edits are not persisted to browser storage. Refreshing loses them.

## Failure and recovery

| Failure | Visible result / action |
|---|---|
| Model loading | Health says loading; extraction returns 503 |
| Model unavailable | Health says failed; inspect startup logs |
| Another active batch | 429; retry once that batch finishes |
| Corrupt/unsupported/large image | Per-card error; remaining cards continue |
| Malformed JSON | Per-card extraction error; no fabricated lead |
| GPU OOM | Per-card error; GPU cache released; reduce image/model budget |
| Polling network failure | UI reconnect action; server work continues |
| Expired job/restart | 404; upload again |
| Edited data invalid | 422 without echoing the submitted PII |
| Unexpected server error | Generic 500 response |
| Excel formula-like content | Saved as literal cell text |

## Reproducibility limits

Direct package versions, the frontend lockfile, and the default model revision
are recorded. Container image digests and hosted package inventories can be
retained when exact deployment reproduction is required.

## Official references

- [Qwen model card](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct)
- [Qwen2-VL alternative](https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct)
- [AWQ checkpoint](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct-AWQ)
- [Transformers AWQ compatibility](https://huggingface.co/docs/transformers/quantization/awq)
- [PyTorch version pairs](https://pytorch.org/get-started/previous-versions/)
- [Compose GPU reservations](https://docs.docker.com/compose/how-tos/gpu-support/)
