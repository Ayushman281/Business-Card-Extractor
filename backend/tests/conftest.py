import time
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import Settings
from app.main import create_app
from app.models.lead import Lead


class FakeExtractor:
    """Only a test double; never used by the production factory."""
    def load(self):
        pass

    def extract(self, image):
        return Lead(first_name="Test", last_name="Person", phone="+44 (0)20 7946 0000")


@pytest.fixture
def image_bytes():
    output = BytesIO()
    Image.new("RGB", (400, 200), "white").save(output, format="JPEG")
    return output.getvalue()


@pytest.fixture(params=["aws", "lightning", "colab"])
def client(request):
    app = create_app(Settings(_env_file=None, execution_target=request.param, enable_model_inference=True), FakeExtractor())
    with TestClient(app) as client:
        for _ in range(100):
            if client.get("/api/health").json()["model_loaded"]:
                break
            time.sleep(0.01)
        else:
            pytest.fail("Test double did not initialize")
        yield client


def wait_for_job(client, job_id):
    for _ in range(200):
        response = client.get("/api/v1/leads/jobs/" + job_id)
        response.raise_for_status()
        job = response.json()
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(0.01)
    pytest.fail("Test batch did not finish")
