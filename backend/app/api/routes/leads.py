import asyncio
import logging
from datetime import datetime, timezone
from pathlib import PurePath

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.datastructures import UploadFile

from app.models.lead import ExportRequest, JobView
from app.services.excel_service import generate_excel
from app.services.image_service import FORMATS, safe_filename
from app.services.job_service import PendingCard

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])
logger = logging.getLogger(__name__)


@router.post("/extract", status_code=202, response_model=JobView)
async def extract(request: Request):
    if request.app.state.model_state != "ready":
        raise HTTPException(503, "Qwen is not ready. Wait for model initialization or contact the server operator.")
    jobs = request.app.state.jobs
    settings = request.app.state.settings
    if jobs.admission.locked():
        raise HTTPException(429, "The server is processing another batch. Please retry shortly.", headers={"Retry-After": "10"})
    await jobs.admission.acquire()
    transferred = False
    cards = []
    try:
        if not request.headers.get("content-type", "").lower().startswith("multipart/form-data"):
            raise HTTPException(415, "Upload images using multipart/form-data.")
        async with request.form(max_files=settings.max_files_per_request, max_fields=0, max_part_size=settings.upload_bytes) as form:
            files = form.getlist("files")
            if not files or any(not isinstance(file, UploadFile) for file in files):
                raise HTTPException(422, "Select at least one image using the files field.")
            if any(key != "files" for key in form.keys()):
                raise HTTPException(422, "Only the files upload field is accepted.")
            for file in files:
                name = safe_filename(file.filename)
                error = None
                data = b""
                if PurePath(name).suffix.lower() not in FORMATS:
                    error = "Unsupported image type. Use JPG, PNG, or WEBP."
                elif file.size is not None and file.size > settings.upload_bytes:
                    error = f"Image exceeds {settings.max_upload_mb} MB."
                else:
                    data = await file.read(settings.upload_bytes + 1)
                    if len(data) > settings.upload_bytes:
                        data = b""
                        error = f"Image exceeds {settings.max_upload_mb} MB."
                cards.append(PendingCard(name, data, error))
        job = jobs.submit(cards)
        transferred = True
        logger.info("batch_accepted count=%d", len(cards))
        return job.view()
    finally:
        if not transferred:
            cards.clear()
            jobs.admission.release()


@router.get("/jobs/{job_id}", response_model=JobView)
async def job_status(job_id: str, request: Request):
    jobs = request.app.state.jobs
    jobs.cleanup()
    job = jobs.jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "These results expired or the server restarted. Please upload the cards again.")
    return job.view()


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str, request: Request):
    jobs = request.app.state.jobs
    job = jobs.jobs.get(job_id)
    if job is not None and job.finished is None:
        raise HTTPException(409, "Wait for this batch to finish before clearing it.")
    jobs.jobs.pop(job_id, None)
    return Response(status_code=204)


@router.post("/export")
async def export(payload: ExportRequest):
    try:
        workbook = await asyncio.to_thread(generate_excel, payload.leads)
    except Exception as exc:
        logger.error("excel_failed category=%s", type(exc).__name__)
        raise HTTPException(500, "Excel could not be generated. Review the edited fields and retry.") from None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Response(
        workbook,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="business_card_leads_{timestamp}.xlsx"'},
    )
