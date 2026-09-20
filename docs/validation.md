# Validation and Evidence Record

Last updated: 2026-09-19.

## Current submission state

The source package is prepared for submission and the user reports that the
full application is deployed in Lightning AI. The submitted public origins are:

- Frontend: <https://5173-01m2w98emjfcmws3qnw3cmh05x.cloudspaces.litng.ai>
- Backend: <https://8000-01m2w98emjfcmws3qnw3cmh05x.cloudspaces.litng.ai>

Lightning public origins depend on the Studio and both processes remaining
available. Availability should be checked immediately before submission.

## Evidence provided during development

- I reported successful real-backend results in hosted Google Colab.
- Lightning AI downloaded both pinned Qwen checkpoint shards, totaling roughly
  7.5 GB, and loaded them successfully.
- The Lightning backend reported `cuda:0`, `dtype=bfloat16`, and
  `model_initialized startup_seconds=26.31`.
- Lightning Port Viewer assigned public HTTPS origins for ports 8000 and 5173.
- The deployment environment was configured for `EXECUTION_TARGET=lightning`,
  explicit model inference, port 8000, API docs, and the port-5173 CORS origin.
- I declared the assignment complete after following the frontend and
  backend startup workflow.

This evidence is user-operated and conversation-reported. The final documentation
pass did not independently control the Lightning account, submit cards, inspect
the final workbook, or capture billing data. Read-only attempts to open the
frontend and readiness URLs through the research browser returned a retrieval
error; live public availability could not be independently established. This
does not establish whether the Studio is offline or access is restricted.

## Source and package review

The development PC was used for source editing and static inspection. The final
documentation/package review checks:

- committed examples keep inference disabled;
- AWS, Lightning AI, and hosted Colab targets are explicit configuration values;
- model loading remains behind both the target and inference-enable guard;
- production construction uses the real Qwen extractor;
- test doubles are confined to the test suite;
- frontend endpoints and schemas match backend routes;
- runtime frontend configuration supports a different backend origin;
- CORS exposes the Excel `Content-Disposition` header;
- source launchers do not rewrite provider-specific Python files;
- `.env`, keys, model weights, caches, generated workbooks, and runtime reports
  are excluded from the final package; and
- packaged source files are compared byte-for-byte with the reviewed workspace
  files after the documentation changes.

No backend, model, Python tests, TypeScript build, or Docker command is executed
on the development PC, in accordance with the project execution policy.

## Runtime checks to retain with the submission

For stronger evidence, retain or capture the following from Lightning before
the evaluation window:

1. `/api/ready` returning `{"ready":true}`.
2. The frontend showing **Qwen is ready**.
3. A fictional mixed-card batch with success/failure counts.
4. Edited results visible in the downloaded XLSX.
5. `.runtime/reports/pytest.txt`, `gpu-check.txt`, and `smoke-report.json`.
6. A browser screenshot and the Studio GPU type.
7. The time at which the public URLs will stop being available.

## AWS boundary

AWS remains a documented alternative deployment. No AWS EC2 resource was created
or accepted during this workflow. The Docker build, NVIDIA container runtime,
Compose smoke test, public AWS URL, AWS memory measurements, and AWS costs must be
validated on AWS before claiming that provider as tested. See
[the AWS deployment guide](../aws/README.md) and [AWS checklist](acceptance.md).
