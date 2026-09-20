"""Prepare, serve and check the same backend on an explicitly selected cloud host.

Never execute on the development PC. Deployment choices belong in .env.
"""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT / "backend"
sys.path.insert(0, str(BACKEND / "scripts"))
from hosted_guard import add_hosted_argument, require_hosted


def environment(args, *, disabled=False):
    env = os.environ.copy()
    env.update({"APP_ENV_FILE": str(args.env_file), "PYTHONPATH": str(BACKEND),
                "PYTHONUNBUFFERED": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1", "TOKENIZERS_PARALLELISM": "false"})
    if disabled:
        env.update({"EXECUTION_TARGET": "disabled", "ENABLE_MODEL_INFERENCE": "false"})
    return env


def run(args, command, *, disabled=False, log=None, timeout=1800):
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    handle = (args.reports_dir / log).open("w", encoding="utf-8") if log else None
    try:
        result = subprocess.run([str(part) for part in command], cwd=BACKEND,
                                env=environment(args, disabled=disabled), timeout=timeout,
                                stdout=handle, stderr=subprocess.STDOUT if handle else None)
    finally:
        if handle:
            handle.close()
        if log:
            print((args.reports_dir / log).read_text(encoding="utf-8", errors="replace")[-16000:])
    result.check_returncode()


def settings(args):
    os.environ["APP_ENV_FILE"] = str(args.env_file)
    sys.path.insert(0, str(BACKEND))
    from app.core.config import Settings
    config = Settings(_env_file=args.env_file)
    if config.execution_target != args.cloud_target or not config.inference_allowed:
        raise RuntimeError(f"Set EXECUTION_TARGET={args.cloud_target} and ENABLE_MODEL_INFERENCE=true in {args.env_file}, on this hosted GPU only. Environment variables override that file.")
    return config


def setup(args):
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        raise RuntimeError("Use Python 3.11–3.13 for the pinned dependencies.")
    if not shutil.which("nvidia-smi"):
        raise RuntimeError("Select an NVIDIA GPU machine before setup.")
    if shutil.disk_usage(PROJECT).free < 30 * 1024**3:
        raise RuntimeError("Keep at least 30 GiB free for dependencies and model weights.")
    if not args.env_file.exists():
        args.env_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT / ".env.example", args.env_file)
        print("Created disabled configuration:", args.env_file)
    else:
        print("Preserving existing configuration:", args.env_file)
    run(args, ["nvidia-smi"], disabled=True, log="nvidia-smi.txt")
    run(args, [sys.executable, "-m", "pip", "install", "--no-cache-dir",
               "-r", BACKEND / "requirements-gpu.txt", "--index-url", args.gpu_index_url], disabled=True)
    run(args, [sys.executable, "-m", "pip", "install", "--no-cache-dir",
               "--index-url", "https://pypi.org/simple", "-r", BACKEND / "requirements.txt",
               "-r", BACKEND / "requirements-model.txt", "-r", BACKEND / "requirements-test.txt"], disabled=True)
    run(args, [sys.executable, "-m", "pip", "check"], disabled=True, log="pip-check.txt")
    run(args, [sys.executable, "-c",
               "import torch, torchvision; from transformers import Qwen2_5_VLForConditionalGeneration; "
               "assert torch.cuda.is_available(), 'CUDA unavailable'; "
               "print(torch.__version__, torchvision.__version__, torch.cuda.get_device_name(0)); "
               "assert torch.ones(1, device='cuda').item() == 1"],
        disabled=True, log="gpu-check.txt", timeout=120)
    run(args, [sys.executable, "-c",
               "import json; from importlib.metadata import distributions; "
               "print(json.dumps(sorted({d.metadata['Name']+'=='+d.version for d in distributions() if d.metadata.get('Name')}), indent=2))"],
        disabled=True, log="package-versions.json", timeout=120)
    if args.run_tests:
        test(args)
    print("Setup finished without loading the model. Configure the cloud target, inference opt-in and CORS in", args.env_file)


def test(args):
    run(args, [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
               "--junitxml=" + str(args.reports_dir / "pytest.xml")],
        disabled=True, log="pytest.txt", timeout=300)


def serve(args):
    config = settings(args)
    with socket.socket() as probe:
        try:
            probe.bind((config.backend_host, config.backend_port))
        except OSError as exc:
            raise RuntimeError("Cannot bind backend port. Check the host/port and stop any existing server before starting another model copy.") from exc
    os.chdir(BACKEND)
    print(f"Starting one worker on {config.backend_host}:{config.backend_port}; wait for /api/ready.", flush=True)
    os.execve(sys.executable, [sys.executable, "-m", "app.serve"], environment(args))


def smoke(args):
    config = settings(args)
    if not Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf").is_file():
        raise RuntimeError("Install fonts-dejavu-core on the hosted server, then rerun smoke.")
    samples = args.reports_dir / "evaluation"
    run(args, [sys.executable, BACKEND / "scripts/generate_samples.py",
               "--cloud-target", args.cloud_target, "--output", samples])
    for name in ("smoke-report.json", "smoke-report.xlsx"):
        (args.reports_dir / name).unlink(missing_ok=True)
    run(args, [sys.executable, BACKEND / "scripts/aws_smoke.py",
               "--cloud-target", args.cloud_target,
               "--base-url", args.base_url or f"http://127.0.0.1:{config.backend_port}",
               "--samples", samples, "--output", args.reports_dir / "smoke-report.json"],
        log="smoke-command.txt", timeout=3300)
    print("Inspect extraction quality and Excel in", args.reports_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("setup", "test", "serve", "smoke"):
        command = commands.add_parser(name)
        add_hosted_argument(command)
        command.add_argument("--env-file", type=Path, default=Path(os.getenv("APP_ENV_FILE", str(PROJECT / ".env"))))
        command.add_argument("--reports-dir", type=Path, default=PROJECT / ".runtime" / "reports")
        if name == "setup":
            command.add_argument("--run-tests", action="store_true")
            command.add_argument("--gpu-index-url", default=os.getenv("GPU_INDEX_URL", "https://download.pytorch.org/whl/cu126"))
        if name == "smoke":
            command.add_argument("--base-url", help="Optional public/reverse-proxy URL instead of loopback")
    args = parser.parse_args()
    require_hosted(args.cloud_target)
    args.env_file = args.env_file.expanduser().resolve()
    args.reports_dir = args.reports_dir.expanduser().resolve()
    {"setup": setup, "test": test, "serve": serve, "smoke": smoke}[args.command](args)


if __name__ == "__main__":
    main()
