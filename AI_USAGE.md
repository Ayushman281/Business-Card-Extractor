# AI Usage Disclosure

## Tools used

ChatGPT was the AI-assisted development tool used for this assignment. Work was
performed with the **Astra 6** and **GPT-5.6 Sol** language models within ChatGPT.
No use of Claude, Cursor, GitHub Copilot, or another code-generation tool is
claimed for this submission.

Both models were used across multiple development iterations. I did not maintain
a model-by-model attribution log, so the recommendations below are attributed to
ChatGPT rather than assigning individual suggestions to Astra 6 or GPT-5.6 Sol.

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

ChatGPT, through Astra 6 and GPT-5.6 Sol, proposed the following recommendations.
I reviewed them, understood their tradeoffs, and adopted them in the project:

- use the pretrained Qwen vision-language model without training or fine-tuning;
- load one model per API process and use one Uvicorn worker to avoid duplicate
  model copies in GPU memory;
- process cards sequentially to fit the intended 16 GB GPU environment;
- use asynchronous HTTP 202 jobs so the React interface can poll and display
  extraction progress;
- validate uploaded images and model-generated JSON before presenting a lead;
- isolate failures by card so one invalid image does not discard the whole batch;
- write spreadsheet values as strings to preserve phone numbers and prevent
  formula-like values from being interpreted by Excel;
- retain uploads and results only temporarily rather than introducing a database
  for this demonstration;
- disable model inference by default and require an explicit hosted-cloud target;
  and
- use environment-based URLs, CORS, cache paths, and ports so the same application
  can run on Lightning AI or AWS without provider-specific source changes.

## Recommendations rejected or modified

I rejected or modified the following ChatGPT-generated recommendations after
reviewing them against the available hardware and deployment requirements:

- ChatGPT initially included local backend and model verification steps. I
  rejected those steps because my development computer did not have sufficient
  GPU, RAM, or CPU resources, and I chose to run the pretrained model only in
  hosted GPU environments.
- An early ChatGPT-generated deployment design treated AWS as the primary target.
  I modified it to use Lightning AI for the working deployment while retaining an
  AWS path through environment configuration.
- ChatGPT initially proposed applying Lightning-specific patches during
  deployment. I replaced that approach with shared configuration and hosting
  scripts so future AWS deployment does not require rewriting application code.
