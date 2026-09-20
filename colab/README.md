# Colab backend notebook

This notebook is the **legacy workflow for the original unchanged source ZIP**.
Do not upload `business-card-lead-extractor-cloud.zip` to its old patch cell.
The current repository already supports `EXECUTION_TARGET=colab`; its shared
launcher and configuration are described in [portable deployment](../docs/portable-deployment.md).

## Start with your existing ZIP

1. In hosted Google Colab choose **File → Upload notebook** and select
   `business_card_backend.ipynb` from this folder.
2. Choose **Runtime → Change runtime type → T4 GPU**. Do not use a local
   runtime or TPU.
3. Keep your unchanged `business-card-lead-extractor-source.zip` in `/content`.
   Opening a new notebook may give you a different runtime. If the ZIP is
   missing, section 2 prompts you to upload the same file again.
4. Run sections **1–9 in order**, waiting for each cell to finish. Section 7
   starts FastAPI and downloads/loads the pretrained Qwen model on Colab.
5. Section **10** is optional: set `USE_MY_CARDS = True` and use its picker, or
   enter uploaded image paths in `CARD_PATHS`. Review/edit before exporting.
6. Section **11** downloads diagnostic reports. Section **12** stops the backend.

Run one section at a time, not Run all: section 10 needs a deliberate choice
and section 12 stops the process. Stop at the first failed required cell and
inspect its output. Download needed files before deleting the Colab runtime.

## Changes made automatically

**No manual ZIP edits or replacement source ZIP are needed.** The notebook
extracts a separate working copy and patches four files in that copy:

| File under backend/ | Adjustment |
|---|---|
| app/core/config.py | Add explicit `colab` target alongside `aws`; preserve inference opt-in |
| app/services/vlm_service.py | Accept Colab at the loading guard; preserve CUDA requirement |
| scripts/generate_samples.py | Use a `--colab-only` invocation label |
| scripts/aws_smoke.py | Use a `--colab-only` invocation and Colab output label |

Every replacement checks for the expected original text first. The notebook
saves original file copies and a hash manifest in its reports directory;
rerunning the patch cell is supported. It does not alter the original ZIP
or the local repository backend. Older AWS-only instructions in that ZIP
describe the original deployment, superseded for this notebook by the user's
explicit Colab testing request.

The model ID/revision, prompt, seven fields, routes, image processing and
Excel implementation are preserved. The notebook installs dependencies in a
separate virtual environment, using the Dockerfile's PyTorch 2.10.0 /
torchvision 0.25.0 CUDA 12.6 pair. Colab's Python may differ from Docker's
Python 3.11; versions are recorded in the reports.

## What passing cells establish

- The installed GPU stack can allocate on CUDA.
- The existing pytest suite passes using explicitly injected test doubles.
- The real Qwen model loads and FastAPI readiness becomes true.
- Single and mixed-batch HTTP extraction work with progress polling.
- Corrupt images fail independently and field-match diagnostics are recorded.
- Edited Excel export has the expected structure and preserves leading zeros.

Manually compare the extracted fields to the cards and open the workbook.
These checks do not validate Docker, Nginx, React integration or public access.

The API binds to `127.0.0.1:8000` **inside the Colab VM**. Notebook cells make
HTTP requests there. The laptop's React preview cannot reach that address.
This is interactive notebook testing with no public tunnel, web hosting,
Google Drive mount or automatic keep-alive. Free GPU/session availability is
limited; see [Colab's FAQ](https://research.google.com/colaboratory/faq.html).

## Files and recovery

If section 4 reaches a successful `pip check` but fails at `pip freeze`, do
not recreate the environment: installed packages need not be deleted for a
reporting failure. The updated section captures freeze's stdout/stderr and
uses the isolated interpreter's `importlib.metadata` to record name/version
pairs instead. The fallback is an inventory, not an exact freeze lockfile.
The report bundle includes the failure, inventory and provenance. Continue
with section 5 only after setup/reporting completes; import/CUDA checks and
the test suite are still required. The traceback alone does not identify
freeze's underlying cause, and a passing pip check does not establish runtime
compatibility.

If section 4 fails during `python -m venv`, use the updated section 4 cell.
It checks that the environment has both an isolated interpreter and pip,
prints the original creation error, and falls back to the official PyPA
virtualenv zipapp. Only `/content/business-card-backend-venv` is repaired;
the source ZIP, cards, reports and model cache are preserved. Bootstrap logs
and the downloaded zipapp hash are included in the diagnostic report bundle.
The original traceback alone does not identify the exact underlying cause;
a missing ensurepip/venv component is one possible cause. Cloud execution
of this repair remains to be verified in the user's runtime.

- Run folders: `/content/business-card-colab-*`.
- Isolated environment: `/content/business-card-backend-venv`.
- Pretrained weights: `/content/business-card-model-cache`.
- Uploads/reports remain on Colab disk until removed or the runtime is deleted.
  Notebook outputs can include contact information; review before sharing.
- No AWS credentials, `.pem` key or Hugging Face token is required.
- Section 12 releases GPU model memory but keeps cached weights for another
  startup within the same runtime. Deleting the runtime loses all these files.
- A startup timeout does not start another process: inspect section 11, then
  rerun section 7 to keep waiting. If initialization failed, stop with section
  12 before fixing/restarting. Stop before re-extracting or patching source.
- After a polling timeout, call `wait_for_job(last_job_id)` instead of
  submitting again. HTTP 429 means a batch is active; 404 means it expired or
  the backend restarted; 503 means the model is not ready.
- Do not run the standalone Qwen PoC alongside the backend; it would load a
  second model. A new runtime needs the ZIP upload and setup cells again.

## Validation status

Notebook JSON/cell structure and patch compatibility with the supplied ZIP
were inspected statically. No notebook cells, backend, tests or model were
executed on the development PC. Actual Colab results remain pending.

References: [PyTorch version pairs](https://pytorch.org/get-started/previous-versions/),
[Qwen integration](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/qwen2_5_vl).
