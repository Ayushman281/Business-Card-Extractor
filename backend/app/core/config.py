"""No inference is enabled by default, even if CUDA is present."""
import os
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.getenv("APP_ENV_FILE", ".env"), extra="ignore")

    execution_target: Literal["disabled", "aws", "lightning", "colab"] = "disabled"
    enable_model_inference: bool = False
    model_id: Literal[
        "Qwen/Qwen2.5-VL-3B-Instruct", "Qwen/Qwen2-VL-2B-Instruct"
    ] = "Qwen/Qwen2.5-VL-3B-Instruct"
    model_revision: str = "66285546d2b821cf421d4f5eb2576359d3770cd3"
    model_dtype: Literal["auto", "float16", "bfloat16"] = "auto"
    model_cache_dir: Path | None = None
    backend_host: str = "0.0.0.0"
    backend_port: int = Field(default=8000, ge=1024, le=65535)
    max_files_per_request: int = Field(default=20, ge=1, le=20)
    max_upload_mb: int = Field(default=10, ge=1, le=10)
    max_request_mb: int = Field(default=210, ge=1, le=210)
    max_image_dimension: int = Field(default=1800, ge=512, le=3000)
    max_image_pixels: int = Field(default=25_000_000, ge=1, le=40_000_000)
    model_max_pixels: int = Field(default=1_003_520, ge=200_704, le=2_007_040)
    model_max_new_tokens: int = Field(default=512, ge=128, le=1024)
    model_timeout_seconds: int = Field(default=180, ge=10, le=600)
    job_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    max_completed_jobs: int = Field(default=32, ge=1, le=100)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: list[str] = Field(default_factory=list)
    enable_api_docs: bool = False

    @model_validator(mode="after")
    def require_explicit_cloud_target(self):
        if self.enable_model_inference and self.execution_target == "disabled":
            raise ValueError("Inference requires EXECUTION_TARGET=aws, lightning or colab")
        if self.model_cache_dir is not None and not self.model_cache_dir.is_absolute():
            raise ValueError("MODEL_CACHE_DIR must be an absolute path on the hosted server")
        return self

    @property
    def inference_allowed(self) -> bool:
        return self.enable_model_inference and self.execution_target in {"aws", "lightning", "colab"}

    @property
    def upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024
