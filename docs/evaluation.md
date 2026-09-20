# Evaluation and performance record

**No recorded measurements for this revision.** Fill on the actual hosted
AWS/Lightning/Colab runtime after each check. Label the provider; a Lightning
result does not establish AWS Docker acceptance.

| Environment detail | Measured/observed value |
|---|---|
| Commit / image digests | Pending |
| Provider / region / instance or Studio / image | Pending |
| Host RAM / GPU / VRAM / driver | Pending |
| Checkpoint / revision / dtype | Pending |
| Input dimension / pixel / token caps | Pending |
| Cold model download and startup time | Pending |
| Cached restart startup time | Pending |
| Peak GPU allocated memory | Pending |
| Total device memory from nvidia-smi | Pending |
| Peak host/container RAM | Pending |
| Actual compute/storage/IP charges and test duration | Pending |

## Card quality

The synthetic set is an initial correctness check, not a representative
benchmark. Add consented examples spanning fonts, orientation, backgrounds,
layouts, missing fields, languages and international phone formats.

| Card | First | Last | Title | Company | Location | Phone | Email | Correct / 7 | Seconds | Failure notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Standard synthetic | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | |
| Missing fields synthetic | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | |
| Rotated synthetic | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | |

A correctly absent field counts as correct only if the expected value is
actually absent. Review spelling, whitespace and equivalent formatting
separately from exact string matching. Do not claim confidence scores or
accuracy on unseen cards based on these examples.

Record single-card latency separately from full-batch duration. Include failed
cards and describe retry behavior. Use the same image preprocessing and
generation settings when comparing checkpoints or quantization.

## Operational checks

Record request behavior with two simultaneous batches, a corrupt card, a
near-limit image, a restarted backend, an expired job and an edited export.
Save the AWS logs/report/workbook as review evidence without publishing PII.
