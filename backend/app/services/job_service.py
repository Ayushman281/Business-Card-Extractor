"""One active batch, transient images, bounded TTL results. Single API worker."""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field

from app.core.config import Settings
from app.models.lead import CardResult, JobView
from app.services.image_service import ImageValidationError, prepare_image
from app.services.parser_service import ExtractionError, lead_warnings

logger = logging.getLogger(__name__)


@dataclass
class PendingCard:
    filename: str
    data: bytes = b""
    error: str | None = None


@dataclass
class Job:
    id: str
    total: int
    created: float = field(default_factory=time.monotonic)
    finished: float | None = None
    status: str = "queued"
    results: list[CardResult] = field(default_factory=list)
    error: str | None = None

    def view(self) -> JobView:
        success = sum(result.status == "success" for result in self.results)
        return JobView(
            job_id=self.id, status=self.status, total=self.total,
            processed=len(self.results), successful=success,
            failed=len(self.results) - success,
            processing_time_seconds=round((self.finished or time.monotonic()) - self.created, 3),
            leads=self.results, error=self.error,
        )


class JobService:
    def __init__(self, extractor, settings: Settings):
        self.extractor = extractor
        self.settings = settings
        self.admission = asyncio.Lock()
        self.jobs: dict[str, Job] = {}
        self.tasks: set[asyncio.Task] = set()

    def cleanup(self):
        now = time.monotonic()
        for job_id, job in list(self.jobs.items()):
            if job.finished is not None and now - job.finished >= self.settings.job_ttl_seconds:
                self.jobs.pop(job_id, None)
        completed = sorted(
            (job for job in self.jobs.values() if job.finished is not None),
            key=lambda job: job.finished,
        )
        for job in completed[:-self.settings.max_completed_jobs]:
            self.jobs.pop(job.id, None)

    def submit(self, cards: list[PendingCard]) -> Job:
        # Caller transfers ownership of the admission lock and card bytes.
        self.cleanup()
        job = Job(id=uuid.uuid4().hex, total=len(cards))
        self.jobs[job.id] = job
        task = asyncio.create_task(self._run(job, cards))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return job

    def _extract_card(self, index: int, card: PendingCard) -> CardResult:
        started = time.perf_counter()
        image = None
        try:
            if card.error:
                raise ImageValidationError(card.error)
            image = prepare_image(card.data, card.filename, self.settings)
            lead = self.extractor.extract(image)
            return CardResult(
                index=index, source_filename=card.filename, status="success", lead=lead,
                warnings=lead_warnings(lead), processing_time_ms=round((time.perf_counter() - started) * 1000, 2),
            )
        except (ImageValidationError, ExtractionError) as exc:
            error = str(exc)
            logger.warning("card_failed index=%d category=%s", index, type(exc).__name__)
        except Exception as exc:
            error = "This card could not be processed. Please retry with a clearer image."
            logger.error("card_failed index=%d category=%s", index, type(exc).__name__)
        finally:
            card.data = b""
            if image is not None:
                image.close()
        return CardResult(
            index=index, source_filename=card.filename, status="error", error=error,
            processing_time_ms=round((time.perf_counter() - started) * 1000, 2),
        )

    async def _run(self, job: Job, cards: list[PendingCard]):
        job.status = "processing"
        try:
            for index, card in enumerate(cards):
                result = await asyncio.to_thread(self._extract_card, index, card)
                job.results.append(result)
            job.status = "completed"
        except Exception as exc:
            logger.error("batch_failed category=%s", type(exc).__name__)
            job.status = "failed"
            job.error = "The batch was interrupted. Completed cards are available below."
        finally:
            for card in cards:
                card.data = b""
            cards.clear()
            job.finished = time.monotonic()
            self.admission.release()
            self.cleanup()
            logger.info("batch_finished total=%d processed=%d duration_seconds=%.3f",
                        job.total, len(job.results), job.finished - job.created)

    async def close(self):
        # Do not release admission while an inference thread is still running.
        if self.tasks:
            await asyncio.gather(*list(self.tasks), return_exceptions=True)
