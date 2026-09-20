# AWS-only evaluation samples

No sample generator or model is run on the development PC.

On the AWS server, use the synthetic sample generator in
`backend/scripts/generate_samples.py`. It produces three fictional cards
with known fields, different backgrounds, a rotated layout and missing data,
plus a corrupt file. Names and organizations are fictional; email domains are
reserved example domains. Review generated cards before using the accuracy
worksheet.

Extend this small set with consented cards covering different fonts, layouts,
languages and orientations. Do not treat synthetic-card results as a production
accuracy benchmark.

Personal cards belong in an excluded location on the AWS server. Git ignore
does not prevent OneDrive synchronization. No evaluation results exist yet.
