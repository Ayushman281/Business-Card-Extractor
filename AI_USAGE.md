# AI Usage Disclosure

## Tools used

ChatGPT was the AI-assisted development tool used for this assignment. Work was
performed with the **Astra 6** and **GPT-5.6 Sol** language models within ChatGPT.
No use of Claude, Cursor, GitHub Copilot, or another code-generation tool is
claimed for this submission.

## Extent of AI assistance

I estimate that approximately **80% of the submitted code was AI-generated or
materially AI-assisted**. This is my personal estimate rather than a measured
line-by-line attribution. Assistance also covered tests,
infrastructure configuration, and documentation. It is disclosed directly
because the assignment permits AI tools, but I am expected to understand and take
responsibility for the result.

AI assistance covered:

- project architecture and repository organization;
- the React/TypeScript upload, progress, editing, and export interface;
- FastAPI routes, schemas, middleware, and error handling;
- the Qwen VLM loading and structured-extraction adapter;
- image validation and preprocessing;
- asynchronous in-memory batch processing;
- Excel generation and string-safety handling;
- unit-test and hosted smoke-test scaffolding;
- Docker, Compose, Nginx, Lightning AI, Colab, and AWS deployment material;
- debugging of hosted dependency, environment, CORS, and public-port issues; and
- the final README and technical documentation.

## My contribution and responsibility

I did not write every line independently. I manually adapted and corrected the
backend-hosting setup and scripts, configured the Lightning AI runtime, worked
through environment and public-port problems, selected deployment settings, ran
the application in hosted GPU environments, inspected generated outputs, and
reviewed the system's main components and data flow.

I have developed a working understanding of the application: how the frontend
calls the API, why extraction is asynchronous, how the model is loaded, how images
and model output are validated, why GPU concurrency is bounded, how results
expire, how Excel is generated, and how Lightning and AWS deployment paths
differ. I accept responsibility for the submitted code, configuration, operation,
and limitations.

## Recommendations adopted

The following AI recommendations were adopted after review:

- use a pretrained Qwen vision-language model without training or fine-tuning;
- initialize one model per API process and run one Uvicorn worker;
- process cards sequentially to stay within a 16 GB GPU memory budget;
- return HTTP 202 jobs and let the UI poll real progress;
- validate file size, decoded pixels, actual image format, EXIF orientation, and
  model-generated JSON before presenting a lead;
- keep failed cards independent so one bad image does not discard the batch;
- write all exported spreadsheet values as strings;
- keep uploads and results transient, with bounded result retention;
- keep model inference disabled by default and require an explicit cloud target;
- configure provider-specific URLs, CORS, cache locations, and ports through the
  environment instead of hardcoding them in application source; and
- retain a shared implementation that can move from Lightning AI to AWS with
  minimal configuration changes.

## Recommendations rejected or modified

The development plan was changed in the following ways:

- Local CPU/model execution was rejected because the development machine did
  not have sufficient resources and the user explicitly prohibited local model
  execution.
- An initial AWS-only design was generalized after Lightning AI became the
  chosen deployment environment; AWS remains supported through configuration.
- A patch-at-deployment Lightning approach was replaced with native multi-cloud
  configuration to reduce future AWS migration work.

## Verification boundary

I ran the hosted application and supplied the deployment URLs. During the
interaction, Lightning downloaded the pinned checkpoint and reported a successful
model initialization. I also performed the earlier Colab execution. This
documentation pass reviewed source and packaging locally but
did not independently execute the backend, model, or Docker stack. Read-only
public-URL checks were inconclusive, as recorded in `docs/validation.md`.
AWS deployment remains an alternate documented path rather than a claimed AWS
runtime acceptance result.
