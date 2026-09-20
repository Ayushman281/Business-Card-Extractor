# Project execution policy

The user permits a frontend-only local preview to inspect the interface.
Installing frontend dependencies and running the Vite development server on
loopback are allowed. Do not start the backend or connect the preview to a
model service. The user also authorizes backend testing and pretrained-model
inference in a hosted Google Colab GPU runtime using the notebook in colab/.
Full Docker/public-deployment acceptance remains on AWS.
The user also authorizes backend testing and pretrained-model inference in a
hosted Lightning AI GPU Studio using the setup package in lightning/.
The current shared launcher is scripts/cloud_backend.py; lightning/ documents
that flow. Application code must support AWS and Lightning through configuration,
without source patching or provider-specific model implementations.
On the development PC, edit and inspect source, or preview the frontend only.
Do not run backend services, unit tests, typechecks, production builds, Docker,
sample generators, pretrained-model inference, model downloads, training or
fine-tuning. Lightweight dependency metadata/lockfile resolution with install
scripts disabled is allowed; it is not runtime verification.

Backend/model execution belongs on the user's AWS server or explicitly selected
hosted Colab or Lightning AI runtime, never the development PC. Source-only notebook JSON and
patch compatibility inspection is allowed locally; do not execute its cells.
No training or
fine-tuning is required anywhere. Use the pretrained Qwen checkpoint; do not
substitute another vendor or return test doubles from production routes.

Keep inference disabled by default. Preserve the explicit execution target
and inference-enable guards. Record unexecuted checks honestly in
docs/validation.md. Never mark a phase runtime-accepted based only on source
inspection. Keep costs, account quota and regional pricing verified before
creating AWS resources. Follow the user's current instructions over older
references to local testing.
