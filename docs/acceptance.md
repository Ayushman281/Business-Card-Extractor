# Acceptance Checklist

This checklist separates the current Lightning AI submission from the optional
AWS deployment. Tick runtime items only after observing them on the named host.

## Submission artifacts

- [x] Public Lightning frontend URL recorded in the root README.
- [x] Public Lightning backend/readiness and API-doc URLs recorded.
- [x] Final source package prepared without secrets, weights, caches, or `.env`.
- [x] Root README covers setup, architecture, decisions, stack, limitations, and
  future improvements.
- [x] README contains a candid **AI Usage** section naming ChatGPT, Astra 6, and
  GPT-5.6 Sol and disclosing approximately 80% AI-assisted code.
- [x] Dedicated Lightning AI full-stack instructions are included.
- [x] Dedicated AWS frontend/backend deployment instructions are included.
- [x] Application and model license boundaries are documented.

## Lightning AI runtime

- [x] Hosted NVIDIA GPU selected and visible to the runtime.
- [x] Pinned Qwen checkpoint shards downloaded on Lightning.
- [x] Model initialization reported successfully on `cuda:0`.
- [x] Frontend and backend public Port Viewer origins assigned.
- [ ] Recheck `/api/ready` immediately before evaluator access.
- [ ] Confirm the public frontend opens in a signed-out/private browser session.
- [ ] Capture a full fictional-card upload, progress, review, edit, and export run.
- [ ] Open the final XLSX and verify the seven columns and edited values.
- [ ] Retain hosted pytest, GPU, and smoke reports with the submission evidence.
- [ ] Confirm the Studio availability window and stop it after evaluation.

The checked runtime items above reflect evidence reported during the interactive
deployment. I should complete the unchecked evidence items in Lightning
immediately before final delivery.

## Functional review

- [ ] Multi-file picker, drag-and-drop, previews, and removal work.
- [ ] JPG, PNG, and WEBP are accepted within configured limits.
- [ ] Empty, corrupt, mismatched, oversized, animated, and excess files receive
  controlled errors without discarding valid cards.
- [ ] Progress counts match processed, successful, and failed cards.
- [ ] First name, last name, title, company, location, phone, and email match the
  visible fictional test cards after manual review.
- [ ] Missing fields remain blank/null rather than being invented.
- [ ] Table edits appear exactly in the downloaded workbook.
- [ ] International and leading-zero phone values remain text.
- [ ] A second simultaneous batch receives 429 instead of creating parallel GPU
  inference.
- [ ] Clearing a completed batch removes its server result.
- [ ] Browser Console and Network panels show no unexpected CORS, CSP, mixed
  content, or API errors.

## Security and privacy review

- [ ] Use fictional cards for the public unauthenticated demonstration.
- [ ] No credentials, `.env`, private keys, real cards, model weights, or exported
  personal data exist in the source package.
- [ ] Backend logs contain status/timings rather than raw cards, model output, or
  job URLs.
- [ ] Expired and deleted jobs return 404.
- [ ] Only one backend/model process is running.
- [ ] The public backend is HTTPS and only the exact frontend origin is allowed by
  CORS.

## Optional AWS acceptance

All AWS items remain pending until AWS is actually used:

- [ ] Region, instance price, GPU quota, credit applicability, EBS, and public-IP
  costs verified.
- [ ] `g4dn.xlarge` or another measured 16 GB GPU host launched.
- [ ] `bash scripts/aws-preflight.sh --aws-only` passes.
- [ ] `docker compose -f compose.test.yml run --build --rm tests` passes.
- [ ] `docker compose build` passes for frontend and backend.
- [ ] CUDA is visible inside the production backend container.
- [ ] Qwen initializes from the pinned revision and `/api/ready` becomes true.
- [ ] Real HTTP smoke test and manual workbook review pass.
- [ ] Frontend is public while backend port 8000 remains private.
- [ ] HTTPS/domain behavior is verified if real personal data is used.
- [ ] Memory, latency, restart/cache reuse, and actual cost are recorded.
- [ ] EC2 and retained billable resources are stopped or removed after evaluation.

## Sign-off record

Record the final date, reviewer, source-package SHA-256, deployment provider,
machine/GPU type, model revision, public URL, smoke-report location, representative
screenshot, workbook review, and planned shutdown time.
