# FileGuard

Standalone file quarantine and release-workflow prototype. Python standard library only. Independent of SentinelFlow AI; no LLM or cloud credentials are required.

## Run

```sh
python file_guard.py
python attack_replay.py
python -m unittest -v
```

Open the printed HTML report. Generated files and SQLite audit records are saved under file-demo/.

## Flow

Local upload -> quarantine -> basic format and identity checks -> simulated GuardDuty verdict -> approved folder or quarantine -> SQLite metadata and audit history.

Verdicts are bound to object version, opaque ETag and content hash. Non-clean, failed, unsupported, mismatched and tampered cases do not release files. Later threat findings revoke local approval. Replaying a clean verdict cannot reopen a blocked object.

## Important limits

This is not an antivirus engine. The demo injects verdicts; no ClamAV or GuardDuty scan occurs. Headers are basic validation, not full document parsing. attack_replay.py includes an accepted inert instruction-text case to demonstrate that a falsely clean verdict is not detected by the routing layer. Files are never executed or passed to an LLM.

No live S3/database deployment, OCR, sandboxing, continuous monitoring or malware-detection accuracy is claimed. SQLite stores metadata; content stays on local disk. Local filesystem/database changes are not a distributed transaction. See FILE_SECURITY.md for the planned AWS design and production requirements.
