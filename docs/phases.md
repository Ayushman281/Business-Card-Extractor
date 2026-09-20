# Historical implementation phase plan

Update 2026-09-18: the user subsequently authorized frontend-only local preview,
hosted Colab testing, and Lightning AI backend/model hosting. The shared source
now supports Lightning/AWS by environment configuration. This phase table is the
original AWS submission plan; its AWS acceptance gates remain pending. No hosted
test is inferred to pass from the new portability changes. See
[portable deployment](portable-deployment.md) and [validation](validation.md).

Update 2026-09-19: I deployed the full application on Lightning AI,
reported successful model initialization, and recorded public frontend/backend
origins. The table below preserves the earlier AWS-centered planning state; it is
not the current submission-status source. Use the root README and validation
record for current status. AWS runtime acceptance remains optional and pending.

The user's instruction on 2026-09-17 supersedes every original reference to
local model inference, local testing or local production runs. The PC is
used for source preparation only. All model use is pretrained inference,
without training or fine-tuning on either machine.

Implementation can be prepared before EC2 exists. Execution-dependent phase
acceptance remains pending until AWS is available. This distinction avoids
claiming that the application is validated merely because its source is written.

| Phase | Deliverable | Current state |
|---|---|---|
| 0 Architecture and prerequisites | Architecture, model comparison, AWS hardware and execution boundary | Documented; AWS account/quota/price unverified |
| 1 Repository and project structure | Backend/frontend/services/tests/docs, ignore rules | Written in the existing Git repository |
| 2 Qwen VLM proof of concept | AWS-only PoC script and synthetic samples | Written; actual inference pending on AWS |
| 3 Business-card extraction pipeline | Image prep, prompt, parser, nullable schemas | Written; runtime pending |
| 4 FastAPI backend | Lifespan, health/readiness, routing, settings | Written; runtime pending |
| 5 Bulk processing | One active batch, independent failures, progress jobs | Written; runtime pending |
| 6 Excel export | Corrected data, styling, explicit text cells | Written; workbook check pending |
| 7 React frontend | Upload/preview/progress/edit/export, responsive CSS | Written; build and visual QA pending |
| 8 End-to-end integration | Matching API contract and same-origin proxy | Source reviewed; execution pending |
| 9 Error handling and validation | Limits, controlled failures, UI recovery | Written; execution pending |
| 10 Testing | Mocked non-model pytest suite plus real AWS smoke script | Authored, not executed |
| 11 Dockerization | GPU runtime, separate test target, frontend multi-stage build | Written; build pending on AWS |
| 12 Production-style test | Run Compose on AWS loopback before public access | Moved to AWS; pending |
| 13 README + AI Usage + architecture | Setup, decisions, limitations and disclosure | Written; measured results pending |
| 14 Acceptance readiness review | Source review and explicit deferred-check register | Prepared; runtime acceptance pending on AWS |
| 15 AWS server creation | Budgets, account/region/price/quota, EC2 | Guide written; no resources created |
| 16 Server configuration | GPU driver, Docker, NVIDIA Container Toolkit | Guide written; not executed |
| 17 Deploy Dockerized application | AWS build, model PoC, Compose launch | Guide written; not executed |
| 18 Configure Nginx/public access | Proxy config, bind/security group, optional HTTPS | Container config written; public setup pending |
| 19 Public application testing | Browser and second-network checks | Pending |
| 20 Performance/cost checks | Measured timings/memory, actual bill exposure | Templates written; measurements pending |
| 21 Final submission review | Repository, public URL, evidence and docs | Checklist written; submission not complete |
| 22 Technical interview preparation | Explanations and modification exercises | Guide written; practical rehearsal pending |

## Phase 0: goal, design and prerequisites

Build an assessment application that can be explained and deployed on one
AWS GPU host. The seven required lead fields are preserved through extraction,
review and export. Qwen remains the primary semantic extraction engine.

The previously inspected laptop has 15.8 GiB RAM and a 4 GiB GPU; these no
longer determine model selection because it will not execute the application.
Only an editor, Git and SSH/source-transfer access are needed on the PC.
Docker Desktop and a local Python/Node environment are unnecessary.

AWS requires an x86-64 Ubuntu GPU host, working NVIDIA drivers, Docker Engine,
Compose plugin, NVIDIA Container Toolkit, outbound access to registries and
Hugging Face, adequate disk, and a verified billing/quota plan.
Plan around a 16 GiB GPU and 16 GiB host RAM, then measure real usage.

Micro instances lack the memory for billions of unquantized weights and
inference overhead. Free-tier-eligible CPU instances are not a substitute for
a measured GPU plan. No CPU or quantization experiment will be run locally.

## Code and file ownership

Full source is in the repository, rather than fragmented snippets to reassemble.
Use the README project map to follow each layer. The critical paths are:

- Phase 2: `backend/scripts/qwen_poc.py` and `app/services/vlm_service.py`.
- Phase 3: `image_service.py`, `parser_service.py`, `prompt.py`, `models/lead.py`.
- Phases 4–5: `app/main.py`, `api/routes/`, `job_service.py`.
- Phase 6: `excel_service.py`.
- Phases 7–8: `frontend/src/` and `frontend/nginx.conf`.
- Phases 9–10: `core/middleware.py` and `backend/tests/`.
- Phases 11–14: Dockerfiles, Compose files and the validation documents.

## Commands, tests and expected results

All executable build/test commands are in [AWS deployment](aws-deployment.md).
The phase tests and expected outputs are in [acceptance](acceptance.md).
The non-model suite must pass, the frontend must build, readiness must become
true, and the real smoke test must validate a mixed batch and an editable
Excel export before public acceptance can be signed off.

No command that imports the model stack or executes application code is needed
on the development PC.

## Common problems and technical review notes

A disabled inference flag is an intentional guard. A failed CUDA check is an
AWS driver/container issue, not a reason to train a model. Qwen is already
pretrained: inference applies the frozen weights to a new image. Training
would update those weights and is neither needed nor implemented.

A successful source review cannot establish inference accuracy or prove a
Docker image builds. Maintain the distinction between implemented, reviewed,
executed and accepted throughout the assignment.
