"""Hosted smoke check for AWS/Lightning/Colab. Legacy filename retained for AWS commands."""
import argparse
import json
import time
import uuid
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from zipfile import ZipFile
from hosted_guard import add_hosted_argument, require_hosted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_hosted_argument(parser)
    parser.add_argument("--base-url", default="http://frontend")
    parser.add_argument("--samples", type=Path, default=Path("/tmp/evaluation"))
    parser.add_argument("--output", type=Path, default=Path("/tmp/smoke-report.json"))
    args = parser.parse_args()
    require_hosted(args.cloud_target)
    base = args.base_url.rstrip("/")

    def request(path, data=None, content_type=None, method=None):
        headers = {"Content-Type": content_type} if content_type else {}
        with urlopen(Request(base + path, data=data, headers=headers, method=method), timeout=120) as response:
            return response.status, response.read()

    deadline = time.monotonic() + 1800
    while True:
        try:
            request("/api/ready")
            break
        except HTTPError as exc:
            if exc.code != 503 or time.monotonic() >= deadline:
                raise
            time.sleep(5)

    boundary = "card-" + uuid.uuid4().hex
    payload = bytearray()
    filenames = ["standard.png", "missing-fields.png", "rotated.png", "corrupt.jpg"]
    for filename in filenames:
        payload.extend(("--" + boundary + '\r\nContent-Disposition: form-data; name="files"; filename="' + filename + '"\r\nContent-Type: application/octet-stream\r\n\r\n').encode())
        payload.extend((args.samples / filename).read_bytes())
        payload.extend(b"\r\n")
    payload.extend(("--" + boundary + "--\r\n").encode())
    status, body = request("/api/v1/leads/extract", bytes(payload), "multipart/form-data; boundary=" + boundary)
    assert status == 202, "Extraction must return an asynchronous job"
    job_id = json.loads(body)["job_id"]
    deadline = time.monotonic() + 1200
    while True:
        _, body = request("/api/v1/leads/jobs/" + job_id)
        job = json.loads(body)
        if job["status"] in {"completed", "failed"}:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError("The evaluation batch did not finish")
        time.sleep(2)
    assert job["status"] == "completed"
    assert (job["total"], job["processed"], job["successful"], job["failed"]) == (4, 4, 3, 1), "Inspect per-card errors"
    leads = [result["lead"] for result in job["leads"] if result["status"] == "success"]
    leads[0]["company"] = "Reviewed company"
    leads[0]["phone"] = "001234567"
    _, workbook = request("/api/v1/leads/export", json.dumps({"leads": leads}).encode(), "application/json")
    with ZipFile(BytesIO(workbook)) as archive:
        assert archive.testzip() is None
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        text = " ".join(sheet.itertext())
        for expected in ("First Name", "Last Name", "Position / Job Title", "Company", "Location", "Phone Number", "Email Address", "Reviewed company", "001234567"):
            assert expected in text, "Excel field missing: " + expected
    expected = json.loads((args.samples / "expected.json").read_text())
    scores = []
    for result in job["leads"]:
        if result["status"] == "success":
            truth = expected[result["source_filename"]]
            # Exact match diagnostic only; human review decides semantic correctness.
            scores.append({"file": result["source_filename"],
                           "exact_fields": sum(result["lead"].get(key) == value for key, value in truth.items()),
                           "total_fields": 7, "processing_time_ms": result["processing_time_ms"]})
    report = {"checks": "HTTP extraction, mixed batch, edited export and XLSX structure passed",
              "bulk_seconds": job["processing_time_seconds"], "synthetic_exact_matches": scores,
              "quality_review": "Manual review still required"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output.with_suffix(".xlsx").write_bytes(workbook)
    request("/api/v1/leads/jobs/" + job_id, method="DELETE")
    print(f"{args.cloud_target} smoke checks passed. Review the saved report and workbook.")


if __name__ == "__main__":
    main()
