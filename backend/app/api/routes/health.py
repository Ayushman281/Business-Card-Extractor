from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/api/health")
async def health(request: Request):
    state = request.app.state.model_state
    return {"status": "healthy" if state == "ready" else "degraded",
            "api_healthy": True, "model_loaded": state == "ready", "model_state": state}


@router.get("/api/ready")
async def ready(request: Request):
    loaded = request.app.state.model_state == "ready"
    return JSONResponse({"ready": loaded}, status_code=200 if loaded else 503)


@router.get("/api/config")
async def public_config(request: Request):
    settings = request.app.state.settings
    return {"max_files": settings.max_files_per_request, "max_upload_mb": settings.max_upload_mb,
            "job_ttl_seconds": settings.job_ttl_seconds, "accepted_extensions": [".jpg", ".jpeg", ".png", ".webp"]}
