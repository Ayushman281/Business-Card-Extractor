# AWS deployment and first validation

For the primary step-by-step frontend and backend deployment instructions, use
[aws/README.md](../aws/README.md). This document retains additional infrastructure
and proof-of-concept checks. AWS runtime acceptance remains pending.

The backend now shares source with Lightning AI. Migrating to AWS needs environment
changes only: select `EXECUTION_TARGET=aws`, explicitly enable inference, remove
Studio-specific cache paths, leave `API_BASE_URL` empty and restore
`API_PROXY_URL=http://backend:8000`. Use the same Dockerfiles and this guide.
See [the configuration matrix](portable-deployment.md) for a frontend-only AWS
deployment that continues using the Lightning GPU backend.

**Every command in this guide that builds, tests, starts the app or loads Qwen
runs on the AWS server. Never run those commands on the development PC.**
No resources have been created and none of these commands have been executed.

## 1. Cost and account gate — before creating a server

Record the account creation date, plan, remaining credits, expiry and region.
AWS distinguishes accounts created before and on/after 15 July 2025; a
`Free tier eligible` label alone does not establish that a deployment has no
cost. Check [the current EC2 rules](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)
and your Billing console.

In Billing and Cost Management → Budgets, create a zero-spend alert and a small
monthly cost budget (for example USD 5 or 10) to your account email. Enable
Free Tier alerts where available. Check Cost Explorer and active resources.
[Budget notifications can be delayed](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html);
a budget alert is not an automatic spending cap.

The proposed resource is **one paid GPU EC2 instance**, with an EBS root disk
and a public IP when public access is enabled. A candidate is
[g4dn.xlarge](https://aws.amazon.com/ec2/instance-types/g4/): 4 vCPUs, 16 GiB
host RAM and an NVIDIA T4 with 16 GiB GPU memory. Ordinary EC2 micro instances
are unsuitable for this full VLM workload. This application's model runtime
requires CUDA; a CPU-only instance cannot run the extraction backend as supplied.

Before launch, inspect EC2 regional availability and Service Quotas for
Running On-Demand G/VT instances. Mumbai is a candidate, not a fixed choice.
Confirm enough quota for 4 vCPUs. Verify an actual Linux On-Demand price in
the selected region using [AWS pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
or [the calculator](https://calculator.aws/). Avoid Spot interruption during
an evaluator's demo and do not purchase a reservation for this assessment.

Fill this table before launch:

| Item | Verified value |
|---|---|
| Region / instance / AMI | Pending |
| EC2 hourly price | Pending |
| Planned running hours | Pending |
| EBS size / monthly price | Pending |
| Public IPv4 / transfer / tax exposure | Pending |
| Credits applicable and expiry | Pending |
| Maximum expected session cost | Pending |
| Person and time responsible for stopping the instance | Pending |

Estimate: compute rate × running hours + prorated EBS + IP hours + chargeable
egress/tax. Credits may offset eligible usage but do not make GPU compute
intrinsically free. Burstable CPU alternatives may also have CPU-credit charges.

Stopping through EC2 ends running compute charges after the stop completes;
retained EBS volumes, snapshots and allocated IP resources can still cost money.
Terminate after the assessment and explicitly review retained disks, snapshots
and addresses. See [AWS stop/start behavior](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html).
Schedule an availability window with the evaluator before stopping the demo.

## 2. Create EC2 only after the cost gate

EC2 → Instances → Launch instances:

1. Name: `business-card-qwen-app`.
2. AMI: an x86-64 Ubuntu 22.04/24.04 GPU-compatible Deep Learning Base AMI
   with NVIDIA driver, or Ubuntu with the NVIDIA driver installed separately.
   Check the AMI's publisher, SSH username and additional software charges.
3. Instance: the region/quota/price-verified GPU choice, initially g4dn.xlarge.
4. Key pair: create/download `business-card-app-key.pem`. Keep it outside the
   repository and never commit it.
5. Network/security group: SSH 22 from **My IP** only. Keep public web access
   restricted until server validation. Later allow TCP 80 and optionally 443.
   Do not add public rules for 8000 or 8080.
6. Storage: plan an 80 GiB gp3 EBS root disk for OS, CUDA Python wheels,
   Docker layers/build cache and model weights. This is a planning allowance,
   not a measured minimum or a free allowance. Check delete-on-termination
   and actual charges.
7. Require IMDSv2 if using EC2 metadata. The application itself needs no AWS
   access keys or AWS API permissions.
8. Launch and record instance ID/public address. Do not put keys into .env.

From Windows PowerShell, connect (replace the example paths/address):

```powershell
ssh -i 'C:\secure\business-card-app-key.pem' ubuntu@PUBLIC_IP
```

If OpenSSH rejects key permissions, use the key file's Windows Security settings
to remove access for other users and keep your own read access. On Linux/macOS
the equivalent setup normally includes `chmod 400 path/to/key.pem`.

Everything below is in the **SSH terminal on AWS** unless marked otherwise.

## 3. Configure the server

First verify the GPU driver:

```bash
nvidia-smi
```

Stop here if the host cannot see the GPU. Use a suitable NVIDIA driver/AMI and
reboot when its installation requires it. A CUDA wheel is not a host driver.

If Docker is already installed by the AMI, inspect its version and avoid
installing a conflicting second runtime. Otherwise follow
[Docker's official Ubuntu repository installation](https://docs.docker.com/engine/install/ubuntu/).
For a fresh supported Ubuntu host:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$VERSION_CODENAME" "$(dpkg --print-architecture)" | sudo tee /etc/apt/sources.list.d/docker.sources
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Log out and reconnect for group membership to apply. The docker group grants
powerful host access; only add the intended operator.

Install/configure [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
if not already configured:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
docker version
docker compose version
docker run --rm --runtime=nvidia --gpus all ubuntu:24.04 nvidia-smi
```

## 4. Transfer source and configure AWS execution

Use your actual Git repository URL:

```bash
git clone https://github.com/Ayushman281/Business-Card-Extractor.git business-card-lead-extractor
cd business-card-lead-extractor
cp .env.example .env
nano .env
```

Use the repository URL listed in the root README.
Alternatively transfer a source archive excluding .git, .env, keys, caches and
outputs. Never transfer model weights from the PC; none are needed there.

The prepared source ZIP contains the project under a single
`business-card-lead-extractor/` directory. To transfer that ZIP from Windows
PowerShell (source transfer only):

```powershell
scp -i 'C:\secure\business-card-app-key.pem' `
  'C:\path\to\business-card-lead-extractor-final.zip' `
  ubuntu@PUBLIC_IP:~/
```

On AWS, extract it into a fresh directory, then create the environment file:

```bash
sudo apt-get install -y unzip
unzip business-card-lead-extractor-final.zip
cd business-card-lead-extractor
cp .env.example .env
nano .env
```

Change only on AWS:

```dotenv
EXECUTION_TARGET=aws
ENABLE_MODEL_INFERENCE=true
HTTP_BIND=127.0.0.1
HTTP_PORT=8080
```

Keep the provided model ID/revision and limits for the first attempt. Do not
put AWS credentials in .env. Inference requires outbound downloads but no
hosted paid model API.

```bash
bash scripts/aws-preflight.sh --aws-only
docker compose config --quiet
```

## 5. Run the authored non-model tests and build images

These commands may download several gigabytes of dependencies to the AWS disk.

```bash
docker compose -f compose.test.yml run --build --rm tests
docker compose build
docker compose run --rm --no-deps --entrypoint python backend -c \
  'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'
```

The test target does not install PyTorch/Transformers and does not invoke Qwen.
The frontend Docker build performs TypeScript checking and Vite compilation.
Stop and fix failures before moving on. Do not describe the build as verified
until these commands succeed.

## 6. Isolated real Qwen proof of concept

Before starting the API, run one container so no second model competes for VRAM.
This optional proof of concept runs on AWS; the user has already operated the
model in hosted Colab and Lightning environments.

```bash
docker compose run --rm --no-deps --entrypoint sh backend -c '
  python scripts/generate_samples.py --aws-only &&
  python scripts/qwen_poc.py --aws-only --output /tmp/poc-report.json /tmp/evaluation/standard.png &&
  cat /tmp/poc-report.json
'
```

The displayed report contains only the synthetic card data. Review every field
and record the measurements in docs/evaluation.md. The temporary report is
deleted when this one-off container exits; save the displayed results to a
private AWS report if needed. The downloaded weights remain in model-cache.

Do not run this PoC alongside the API: that would create a second model
instance. The PoC's success is not a replacement for HTTP/UI acceptance.

## 7. Start and validate the integrated app on the AWS host

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100 backend
curl -fsS http://127.0.0.1:8080/api/health
curl -fsS http://127.0.0.1:8080/api/ready
```

During loading, health reports `model_state=loading`, and readiness returns
503. Expected after successful initialization: `model_loaded=true` and
readiness `{"ready":true}`. Model-load failures are visible in backend logs.

Generate synthetic images in the running backend, then exercise the real API:

```bash
docker compose exec backend python scripts/generate_samples.py --aws-only
docker compose exec backend python scripts/aws_smoke.py --aws-only
mkdir -p outputs
docker compose cp backend:/tmp/smoke-report.json outputs/smoke-report.json
docker compose cp backend:/tmp/smoke-report.xlsx outputs/smoke-report.xlsx
docker compose cp backend:/tmp/evaluation outputs/evaluation
```

Expected: smoke checks pass, all four files are processed, the corrupt file
fails independently, three cards produce structured responses, and Excel
contains the edited company and leading-zero phone. Exact-match field counts
are diagnostics, not a guarantee of quality. Open the workbook and visually
review the cards using the AWS test environment or the evaluator's chosen
review device.

Measure memory and restart behavior on AWS:

```bash
nvidia-smi
docker stats --no-stream
docker compose exec backend python -m pip freeze
docker compose images
docker compose restart backend
docker compose logs --tail=100 backend
curl -fsS http://127.0.0.1:8080/api/ready
```

Wait for readiness after restart. Model files should be reused from the cache;
online metadata requests can still occur. Completed/in-progress jobs do not
survive restart. Repeat the smoke test after regenerating samples if needed.

## 8. Enable public HTTP after server checks pass

For a temporary demonstration using fictional cards, set `HTTP_BIND=0.0.0.0`
and `HTTP_PORT=80` in .env, then recreate the frontend:

```bash
docker compose up -d --force-recreate frontend
```

Allow inbound TCP 80 on the EC2 security group. Visit `http://PUBLIC_IP/` from
a browser and another network. Keep SSH restricted to your IP and port 8000
closed. Docker port publishing can bypass host UFW expectations; the EC2
security group remains essential. Do not expose the Docker socket.

A public URL has not been created by writing these instructions. Record it in
README only after verifying it.

## 9. Optional HTTPS

Use a domain you control, point its A record at the server address, allow 80/443,
and keep Compose bound to `127.0.0.1:8080`. A host Nginx server can proxy that
address while Certbot manages the domain certificate. Do not run host Nginx
on port 80 while the container also binds port 80.

A minimal host location needs `proxy_pass http://127.0.0.1:8080;`,
`client_max_body_size 210m;`, `proxy_request_buffering off;` and suitable
timeouts. Follow the current [Certbot Nginx instructions](https://certbot.eff.org/instructions)
for the chosen OS. The domain-specific configuration/certificate is not
included because no domain has been provided.

## 10. Troubleshooting

| Symptom | Action |
|---|---|
| Model disabled | Edit both inference flags on AWS and recreate backend |
| CUDA unavailable | Check host nvidia-smi, toolkit and Compose GPU reservations |
| 401/403/404 during download | Verify exact checkpoint/revision and network access; do not silently switch models |
| First startup slow | Inspect logs and disk/network; do not repeatedly restart downloads |
| Permission denied in cache | Inspect named-volume ownership; runtime UID is 10001 |
| Out of memory | Check other GPU processes, pixel/token limits and host memory; avoid multiple PoC/API instances |
| 429 | Wait for active batch or Nginx rate limit; avoid repeated retries |
| 413 | Reduce per-card or aggregate upload sizes |
| Bad/missing fields | Compare visible image, preprocessing and prompt; review manually |
| Public page unreachable | Check EC2 address, security group, bind, port conflict and frontend logs |
| Job 404 | Results expired or server restarted; upload again |
| Disk filling | Inspect docker system df and caches; prune only known unused resources |

## 11. Stop and clean up

On AWS, `docker compose down` stops the app but **does not stop EC2 charges**.
Stop the EC2 instance in the console when the test/demo window ends. Preserve
the named cache volume while iterating; `docker compose down -v` deletes it
and forces a new model download, so do that only for intentional cleanup.

After the assessment, terminate EC2 if no longer needed. Check EBS volumes,
snapshots, Elastic/public IP allocations and every region for retained resources.
Confirm billing after cleanup and keep evidence of the test window/costs.
