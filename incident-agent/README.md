# SentinelFlow AI

AI-assisted cloud incident investigation and file-security workflows.

A local portfolio prototype with optional local LLM, lexical RAG and a minimal stdio MCP tool server. Python standard library only.

## File upload security demo

Run `python file_guard.py` to demonstrate quarantine -> simulated GuardDuty result -> approved storage or blocked review, with SQLite metadata and audit records. See [FILE_SECURITY.md](FILE_SECURITY.md) for implementation, limits and the planned AWS deployment. This is a routing prototype, not a malware scanner. It does not call AWS or detect malware itself.

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

Without a model, the demo uses explicit rules, not an LLM. With a model, the investigator retrieves local runbook documents and generates a summary plus advisory solution suggestions. This is a bounded investigation workflow, not autonomous cloud remediation.

## LLM + RAG solution suggestions

```powershell
python agent.py --scenario database --model llama3.2:1b
```

Add or edit Markdown files under `knowledge/` to extend the knowledge base. Retrieval ranks documents by lexical token overlap; it does not use embeddings or a vector database. All three current runbooks can be returned as context. Documents are loaded fresh per investigation, with content hashes recorded. Generated suggestions include an action, rationale, verification step and document ID citations. Citation IDs are validated; semantic faithfulness still needs human review. Recommendations are never executed. Unknown/conflicting evidence suppresses model mitigation suggestions. A timeout, invalid JSON or invalid citation falls back to deterministic checks.

The local Llama 3.2 1B model is intended for a lightweight demonstration, not production-grade incident judgment. The integration uses Ollama structured JSON output. Local model requests have a 90-second timeout; usage counts and elapsed time appear in traces.

Flow: evidence -> hypothesis -> runbook retrieval -> local LLM -> output validation -> human-review report. MCP is an optional access interface, not a replacement for RAG or an LLM.

## MCP client configuration

Start the minimal local stdio server with `python mcp_server.py`. In a compatible MCP client's server configuration, use your absolute Python executable as `command` and the absolute path to `mcp_server.py` as the sole `args` entry. Set `OLLAMA_MODEL=llama3.2:1b` in that server's environment to enable AI recommendations. The server is not automatically registered in any client.

Exposed tools:
- `search_runbooks`: returns matching local documents.
- `investigate_dummy_incident`: accepts database, memory or unknown; writes a local report. No cloud calls or remediation.

The minimal implementation supports initialization, ping, tools/list and tools/call over newline-delimited JSON-RPC. A subprocess smoke test covers initialization, discovery and runbook search; full client interoperability is not certified. See https://modelcontextprotocol.io/specification/2025-11-25/server/tools and https://docs.ollama.com/api/generate.

## Implemented

- Three fixtures: database saturation, memory pressure, unknown cause.
- Runbook cache with five-minute TTL and versioned key. Live evidence is never cached.
- Model timeout/error fallback to rules; fallback is visible in the report.
- Per-run activity trace with duration, cache hit, mode and error type.
- Draft incident update and recommendations, with unknown causes escalated.
- Escaped HTML output; no model text executed as code.

## Limits and next steps

Read-only CloudWatch Logs support is implemented in `cloud_logs.py`, but live access is unverified: the local AWS CLI has no configured credentials. No Jira or Statuspage integration; no external messages or infrastructure changes. Model success is tested with a mock, not a live installed model. Production requires scoped credentials, sensitive-data redaction, stronger validation and evaluation on real incidents. Human review is required for fixes and customer updates.

## Dummy CloudWatch-format cases

Run `python cloud_logs.py`, then open `demo-results.html`. Five cases cover database errors, OOM termination, ambiguous timeouts, conflicting signals and empty logs. Logs are synthetic local fixtures, not fetched from AWS. The database case also simulates a model timeout. Metrics are never fabricated.

## Live CloudWatch read

Configure AWS CLI authentication locally, then run:

```powershell
python cloud_logs.py --live --log-group /your/test/log-group --region ca-central-1 --profile YOUR_PROFILE --minutes 15
```

Requires `logs:FilterLogEvents` on the selected log group. Reads up to 500 events in the chosen time window; discloses truncated results. No resources are created or modified. Failed AWS reads raise errors rather than substitute dummy data. Reports persist collected logs locally; start with non-sensitive test logs. Optional `--model INSTALLED_MODEL` enables Ollama summaries.

AWS reference: https://docs.aws.amazon.com/cli/latest/reference/logs/filter-log-events.html
