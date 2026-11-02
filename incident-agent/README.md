# Incident investigation agent

A local portfolio prototype, using simulated incidents. Python standard library only.

## Run

```powershell
python agent.py --scenario database
python agent.py --scenario memory
python agent.py --scenario unknown
python agent.py --simulate-model-failure
python -m unittest -v
```

On this computer, if `python` is unavailable, use:
`& 'C:\Users\Dell\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' agent.py`

Each run prints the location of an HTML report. Open it in a browser. JSON reports and JSONL traces are stored under `runs/`.

## Optional local LLM

With Ollama running locally and a model already installed:

```powershell
python agent.py --scenario database --model YOUR_INSTALLED_MODEL
```

Uses the documented local `/api/generate` endpoint with JSON output and a 20-second timeout:
https://docs.ollama.com/api/generate

Without a model, the demo uses explicit rules, not an LLM. With a model, evidence collection and runbook selection remain deterministic; the LLM produces an advisory summary. This is a bounded investigation workflow, not autonomous cloud remediation.

## Implemented

- Three fixtures: database saturation, memory pressure, unknown cause.
- Runbook cache with five-minute TTL and versioned key. Live evidence is never cached.
- Model timeout/error fallback to rules; fallback is visible in the report.
- Per-run activity trace with duration, cache hit, mode and error type.
- Draft incident update and recommendations, with unknown causes escalated.
- Escaped HTML output; no model text executed as code.

## Limits and next steps

No AWS, Jira, or Statuspage integration yet; no external messages or infrastructure changes. Model success is tested with a mock, not a live installed model. Logs are synthetic; production use requires scoped credentials, sensitive-data redaction, input limits, stronger output validation, persistent audit storage, and evaluation on real incidents. Human review is required for proposed fixes and customer updates. This prototype does not automatically set incident severity or claim confirmed root cause.
