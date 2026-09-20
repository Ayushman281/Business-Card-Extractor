import threading
import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.services.vlm_service import QwenLeadExtractor
from conftest import FakeExtractor, wait_for_job


def test_health_disabled_does_not_load_model():
    with TestClient(create_app(Settings(_env_file=None, enable_model_inference=False))) as client:
        assert client.get("/api/health").json()["model_state"] == "disabled"
        assert client.get("/api/ready").status_code == 503
        assert client.post("/api/v1/leads/extract").status_code == 503


def test_cloud_guard_precedes_model_import():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, enable_model_inference=True, execution_target="disabled")
    with pytest.raises(RuntimeError, match="disabled"):
        QwenLeadExtractor(Settings(_env_file=None, enable_model_inference=False)).load()


@pytest.mark.parametrize("target", ["aws", "lightning", "colab"])
def test_cloud_target_still_requires_opt_in(target):
    disabled = Settings(_env_file=None, execution_target=target, enable_model_inference=False)
    with pytest.raises(RuntimeError, match="disabled"):
        QwenLeadExtractor(disabled).load()
    assert Settings(_env_file=None, execution_target=target, enable_model_inference=True).inference_allowed


def test_unknown_target_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, execution_target="local", enable_model_inference=True)


def test_environment_overrides_selected_file(tmp_path, monkeypatch):
    config_file = tmp_path / "deployment.env"
    config_file.write_text("EXECUTION_TARGET=lightning\nENABLE_MODEL_INFERENCE=true\nBACKEND_PORT=8100\n")
    monkeypatch.delenv("EXECUTION_TARGET", raising=False)
    monkeypatch.delenv("ENABLE_MODEL_INFERENCE", raising=False)
    monkeypatch.delenv("BACKEND_PORT", raising=False)
    assert Settings(_env_file=config_file).execution_target == "lightning"
    assert Settings(_env_file=config_file).backend_port == 8100
    monkeypatch.setenv("EXECUTION_TARGET", "aws")
    assert Settings(_env_file=config_file).execution_target == "aws"


def test_cross_origin_preflight_export_and_rejected_origin():
    settings = Settings(_env_file=None, execution_target="lightning", enable_model_inference=False,
                        cors_origins=["https://cards.example.org"])
    with TestClient(create_app(settings)) as client:
        headers = {"Origin": "https://cards.example.org", "Access-Control-Request-Method": "POST",
                   "Access-Control-Request-Headers": "content-type"}
        response = client.options("/api/v1/leads/export", headers=headers)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://cards.example.org"
        export = client.post("/api/v1/leads/export", headers={"Origin": headers["Origin"]},
                             json={"leads": [{"company": "Reviewed"}]})
        assert export.status_code == 200
        assert "Content-Disposition" in export.headers["access-control-expose-headers"]
        headers["Origin"] = "https://unapproved.example.org"
        assert client.options("/api/v1/leads/export", headers=headers).status_code == 400


def test_health_and_mixed_batch(client, image_bytes):
    assert client.get("/api/ready").status_code == 200
    response = client.post("/api/v1/leads/extract", files=[
        ("files", ("good.jpg", image_bytes, "image/jpeg")),
        ("files", ("bad.png", b"not an image", "image/png")),
    ])
    assert response.status_code == 202
    job = wait_for_job(client, response.json()["job_id"])
    assert (job["total"], job["processed"], job["successful"], job["failed"]) == (2, 2, 1, 1)
    assert job["leads"][0]["lead"]["first_name"] == "Test"
    assert job["leads"][1]["lead"] is None
    assert "traceback" not in str(job).lower()
    assert client.delete("/api/v1/leads/jobs/" + job["job_id"]).status_code == 204
    assert client.get("/api/v1/leads/jobs/" + job["job_id"]).status_code == 404


def test_export_uses_edited_values(client):
    result = client.post("/api/v1/leads/export", json={"leads": [{"company": "Edited company", "phone": "00123"}]})
    assert result.status_code == 200
    assert result.content[:2] == b"PK"
    assert ".xlsx" in result.headers["content-disposition"]
    assert result.headers["cache-control"] == "no-store"


def test_invalid_export_does_not_echo_personal_data(client):
    response = client.post("/api/v1/leads/export", json={"leads": [{"email": {"secret": "person@example.org"}}]})
    assert response.status_code == 422
    assert "person@example.org" not in response.text
    assert client.post("/api/v1/leads/export", json={"leads": []}).status_code == 422


def test_no_files_and_unsupported_type(client):
    assert client.post("/api/v1/leads/extract", json={}).status_code == 415
    response = client.post("/api/v1/leads/extract", files=[("files", ("card.exe", b"MZ", "application/octet-stream"))])
    job = wait_for_job(client, response.json()["job_id"])
    assert job["failed"] == 1


def test_busy_batch_is_rejected_without_parallel_inference(image_bytes):
    unblock = threading.Event()

    class BlockingExtractor(FakeExtractor):
        def extract(self, image):
            if not unblock.wait(timeout=5):
                raise RuntimeError("Test wait expired")
            return super().extract(image)

    app = create_app(Settings(_env_file=None, execution_target="aws", enable_model_inference=True), BlockingExtractor())
    with TestClient(app) as client:
        try:
            for _ in range(100):
                if client.get("/api/ready").status_code == 200:
                    break
                time.sleep(0.01)
            first = client.post("/api/v1/leads/extract", files={"files": ("one.jpg", image_bytes)})
            assert first.status_code == 202
            second = client.post("/api/v1/leads/extract", files={"files": ("two.jpg", image_bytes)})
            assert second.status_code == 429
            assert client.delete("/api/v1/leads/jobs/" + first.json()["job_id"]).status_code == 409
        finally:
            unblock.set()
        assert wait_for_job(client, first.json()["job_id"])["successful"] == 1


def test_request_body_limit():
    with TestClient(create_app(Settings(_env_file=None, max_request_mb=1))) as client:
        response = client.post("/api/v1/leads/export", content=b"x" * (1024 * 1024 + 1))
        assert response.status_code == 413


def test_initialization_failure_is_visible():
    class BrokenExtractor(FakeExtractor):
        def load(self):
            raise RuntimeError("Test failure")
    with TestClient(create_app(Settings(_env_file=None, execution_target="aws", enable_model_inference=True), BrokenExtractor())) as client:
        for _ in range(100):
            response = client.get("/api/health")
            if response.json()["model_state"] == "failed":
                break
            time.sleep(0.01)
        assert response.json()["model_state"] == "failed"
        assert "Test failure" not in response.text
        assert client.get("/api/ready").status_code == 503
