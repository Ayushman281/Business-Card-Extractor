# Technical review preparation

Explain the deployed behavior from the actual system and distinguish it from
upstream benchmarks or future improvements.

## Explain the system in one minute

A user uploads business-card images through a React application. Nginx serves
the frontend and proxies FastAPI. The backend validates each image and sends
it through a pretrained Qwen vision-language model. One batch runs at a time,
and the browser polls real progress. Model text is parsed and schema-validated.
The user reviews/edits the nullable fields, then exports a text-safe Excel file.
Images are transient and the model is cached on the hosted GPU server. Nothing is
trained; the development PC only holds source.

## Questions and defensible answers

1. **Why a VLM instead of OCR?** The task requires Qwen; a VLM can interpret
   layout and associate text with semantic fields in one pass. It can still
   misread or misclassify text, so manual review is required.
2. **Why Qwen?** It is an explicit assessment requirement. There is no silent
   substitute using another model or OCR service.
3. **Why the 3B checkpoint?** It is the preferred checkpoint in the brief and
   a smaller deployment target than the 7B/72B variants and fits the intended
   16 GB GPU deployment profile.
4. **How much memory?** Billions of weights plus vision/KV/activation buffers
   require gigabytes. We plan a 16 GiB GPU but must report measured peak usage,
   not just multiply the model's marketing parameter size.
5. **Why quantization?** It can reduce weight memory, with compatibility and
   accuracy tradeoffs. We did not adopt AWQ before measuring its value.
6. **What accuracy problems can occur?** Stylized layouts, glare, small text,
   handwriting, and ambiguous names can reduce extraction quality, so the UI
   requires manual review before export.
7. **How does the prompt reduce invention?** It asks for visible text only,
   nulls for missing/uncertain fields and no following instructions on cards.
   These are mitigations, not guarantees.
8. **How do you guarantee JSON?** We do not guarantee the model always emits
   valid JSON. We accept recoverable JSON, validate it and return a controlled
   error otherwise.
9. **What if a field is invisible?** It remains null and exports as blank.
10. **What if one card fails?** It gets an error row; other cards continue.
11. **Why FastAPI?** Typed request/response models, async endpoints and lifespan
    management suit this API.
12. **Why React?** Upload previews, polling and editable form state are easy
    to separate into maintainable components.
13. **Why Docker?** It packages dependencies and deployment boundaries; it
    still depends on a compatible host GPU driver.
14. **Why Nginx?** Static assets, same-origin routing, upload limits and a
    public entry point with no exposed backend port.
15. **Why not Lambda?** This design needs a resident GPU VLM; Lambda is not
    the GPU host used for this workload and would change the architecture.
16. **Why not ECS?** It adds orchestration that this single-instance
    assessment does not require.
17. **Why not SageMaker?** Managed inference may be useful later, but brings
    another deployment/cost model beyond this small EC2 demonstration.
18. **Why not Textract?** It would not satisfy the required Qwen extraction.
19. **How is concurrency controlled?** One API worker, one admission lock,
    sequential batch processing, and a model-level lock.
20. **How would 10,000 cards work?** Use durable object storage and a job
    queue, authenticated tenants, separate inference workers, backpressure
    and measured GPU batching. Do not simply add Uvicorn workers.
21. **How is PII protected?** Temporary images, short-lived in-memory results,
    no content logs, no-store responses and HTTPS for real personal data.
    This demo still lacks authentication and durable tenant isolation.
22. **How would authentication fit?** Authenticate at the API boundary, bind
    job ownership to a user/tenant and enforce authorization on every lookup
    and export.
23. **How would latency improve?** Measure first, then consider pixel/token
    limits, dtype, quantization and batches. Preserve small-text readability.
24. **How would accuracy improve?** Build a representative consented
    evaluation set, inspect errors, tune prompts/preprocessing and compare
    model revisions/checkpoints with unchanged scoring.
25. **How would monitoring work?** Aggregate startup/latency/error/OOM/queue
    metrics without logging PII; alert on readiness failures and cost.
26. **How would high availability work?** Move jobs out of process, persist
    necessary state securely, add multiple inference hosts and health-aware
    routing. The current single host is not highly available.
27. **Why a T4-class GPU?** It provides 16 GB of VRAM for the selected 3B model
    while remaining practical for a demonstration deployment.
28. **What does it cost?** Lightning usage depends on the account's GPU allowance;
    AWS cost depends on the selected region, instance runtime, storage, public IP,
    and data transfer.
29. **Biggest current limitation?** The demonstration has no authentication or
    durable job storage, and it processes one batch at a time.
30. **Which parts were AI-assisted?** Architecture, implementation, tests,
    documentation and static review; explain and own each part you demonstrate.

## Follow the code during review

Start at api/routes/leads.py, then job_service.py, image_service.py,
vlm_service.py, parser_service.py and models/lead.py. Trace export from
ResultsTable.tsx through App.tsx and api.ts to excel_service.py.

Demonstrate why no weights load when the inference flag is disabled. Explain
why a valid JSON object can still contain wrong information. Show a corrupt
card beside successful cards, edit a phone value, and verify Excel preserves it.

## Modification exercises — execute and test on AWS only

- Add website or LinkedIn: extend Lead, FIELDS, prompt, TypeScript fields/types,
  Excel headers/widths, fixtures and tests together. Update expected JSON.
- Add CSV: add a route and export service; account for spreadsheet-formula
  injection and preserve phone strings.
- Change upload limits: coordinate Settings bounds, .env, frontend config,
  Nginx body size, tmpfs capacity and host memory.
- Change model: update checkpoint and revision, loader class if necessary,
  model license record, then rerun the same AWS evaluation set.
- Add a request metric: log route categories and durations without capability
  URLs or card contents.
- Add a version endpoint: expose the application version/commit without
  credentials or environment details.
- Change table order: update display configuration while keeping the API and
  required Excel column order deliberate.
- Introduce cancellation: explain why cancelling an asyncio task does not
  necessarily stop a CUDA operation; design safe worker isolation first.
