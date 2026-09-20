import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.routes import health, leads
from app.core.config import Settings
from app.core.logging import configure_logging
from app.core.middleware import RequestLimitsMiddleware
from app.services.job_service import JobService
from app.services.vlm_service import QwenLeadExtractor

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, extractor=None) -> FastAPI:
    config = settings or Settings()
    configure_logging(config.log_level)
    model = extractor if extractor is not None else QwenLeadExtractor(config)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.model_state = "disabled"
        application.state.settings = config
        application.state.jobs = JobService(model, config)

        async def initialize():
            application.state.model_state = "loading"
            try:
                await asyncio.to_thread(model.load)
                application.state.model_state = "ready"
            except Exception:
                application.state.model_state = "failed"
                logger.exception("model_initialization_failed")

        async def expire_results():
            while True:
                await asyncio.sleep(30)
                application.state.jobs.cleanup()

        loader = asyncio.create_task(initialize()) if config.enable_model_inference else None
        reaper = asyncio.create_task(expire_results())
        logger.info("api_started execution_target=%s", config.execution_target)
        try:
            yield
        finally:
            reaper.cancel()
            with suppress(asyncio.CancelledError):
                await reaper
            await application.state.jobs.close()
            if loader:
                await loader
            application.state.jobs.jobs.clear()

    application = FastAPI(
        title="Business Card Lead Extractor", version="1.0.0", lifespan=lifespan,
        docs_url="/docs" if config.enable_api_docs else None,
        redoc_url=None, openapi_url="/openapi.json" if config.enable_api_docs else None,
    )
    application.add_middleware(RequestLimitsMiddleware, max_bytes=config.max_request_mb * 1024 * 1024)
    if config.cors_origins:
        application.add_middleware(
            CORSMiddleware, allow_origins=config.cors_origins,
            allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"],
            expose_headers=["Content-Disposition", "Retry-After"],
        )

    @application.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError):
        return JSONResponse({"detail": "Invalid request. Lead fields must be text or null, with at most 500 characters per field and 20 leads."}, status_code=422)

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)

    @application.exception_handler(Exception)
    async def server_error(request: Request, exc: Exception):
        logger.error("request_failed category=%s", type(exc).__name__)
        return JSONResponse({"detail": "The server could not complete this request. Please retry."}, status_code=500)

    application.include_router(health.router)
    application.include_router(leads.router)
    return application


app = create_app()
