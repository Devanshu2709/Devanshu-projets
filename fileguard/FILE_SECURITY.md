# File security workflow prototype

Run `python file_guard.py` and open the printed report path. No dependencies beyond Python are required. All sample files are harmless text. Injected GuardDuty-shaped events exercise routing; this is NOT a malware scanner, and the simulation cannot establish malware detection accuracy.

## Implemented locally

1. Copy an upload into a quarantine directory with an opaque version ID.
2. Store original filename, version, opaque ETag, SHA-256, validation and state in SQLite.
3. Validate supported PDF, PNG, JPEG or UTF-8 text formats using basic headers/encoding and a 10 MiB limit. Headers are not full document validation.
4. Process a simulated GuardDuty EventBridge event. Require matching bucket, key, version and ETag. Recheck the content hash.
5. Release only COMPLETED + NO_THREATS_FOUND + valid unchanged content. Keep every other verdict quarantined. Blocked versions require manual review; a later clean event cannot reopen them. A later threat event removes the local approved copy.
6. Record each decision. Repeated clean events do not create duplicate approved files. Files remain on disk; the database stores metadata, not executable content.

The local event generator and processor are test utilities, not an authenticated network endpoint. Envelope field matching is not cryptographic authentication. Filesystem and SQLite updates are not a distributed transaction. Local files must not be served directly as a production download system. The optional LLM/RAG incident advisor never overrides file release decisions.

## Planned AWS deployment (not deployed)

Private versioned quarantine S3 -> GuardDuty Malware Protection for S3 -> restricted EventBridge rule -> SQS/Lambda -> validated release decision -> private approved S3 + database metadata.

Before deployment:
- Enable GuardDuty Malware Protection for the quarantine bucket; configure its service role and KMS access if applicable.
- Enforce authenticated uploads, private buckets, versioning and scoped IAM. Users must not copy directly into approved storage or write trusted verdict tags.
- Restrict EventBridge/Lambda/SQS invocation permissions and validate account, region, resource and object identity. An event body alone is not trusted.
- Use exact S3 VersionId when reading/copying; never release whichever object happens to be latest. Treat ETag as an opaque identifier, not a universal content hash.
- Use durable idempotency, conditional database updates, retries and dead-letter queues. Gate reads on current approval state, reconcile partial failures, and consider later rescan revocations.
- Keep unsupported, encrypted, failed and timed-out scans blocked. Define rescan and manual-review policies.
- Add isolated parsing/OCR and content checks before ingestion. No OCR, sensitive-data detection, sandbox detonation or runtime detection is implemented here.
- Do not send customer documents to an LLM without an approved data policy. Uploaded content is untrusted, including prompt-like instructions.

The managed scanner, not this program or its LLM, supplies malware verdicts. GuardDuty updates detection independently. Advanced/unknown malware can evade scanning; additional sandboxing and runtime monitoring require separate integrations. No AWS resources, paid services or live scans were created during this build.

Reference event schema: https://docs.aws.amazon.com/guardduty/latest/ug/monitor-with-eventbridge-s3-malware-protection.html
