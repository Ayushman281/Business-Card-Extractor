"""Hosted real inference proof of concept. Never run on the development PC."""
import argparse
import json
import time
from pathlib import Path
from hosted_guard import add_hosted_argument, require_hosted

from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.image_service import prepare_image
from app.services.vlm_service import QwenLeadExtractor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_hosted_argument(parser)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("images", type=Path, nargs="+")
    args = parser.parse_args()
    require_hosted(args.cloud_target)
    settings = Settings()
    if settings.execution_target != args.cloud_target:
        parser.error("The selected cloud target must match EXECUTION_TARGET.")
    configure_logging(settings.log_level)
    extractor = QwenLeadExtractor(settings)
    extractor.load()
    import torch

    torch.cuda.reset_peak_memory_stats()
    results = []
    for path in args.images:
        started = time.perf_counter()
        image = None
        try:
            if path.stat().st_size > settings.upload_bytes:
                raise ValueError("Image exceeds the configured upload limit")
            image = prepare_image(path.read_bytes(), path.name, settings)
            lead = extractor.extract(image)
            results.append({"file": path.name, "lead": lead.model_dump(), "seconds": time.perf_counter() - started})
        except Exception as exc:
            results.append({"file": path.name, "error_type": type(exc).__name__, "seconds": time.perf_counter() - started})
        finally:
            if image is not None:
                image.close()
    report = {
        "model": settings.model_id, "revision": settings.model_revision,
        "device": torch.cuda.get_device_name(0), "dtype": extractor.dtype,
        "startup_seconds": extractor.startup_seconds,
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
