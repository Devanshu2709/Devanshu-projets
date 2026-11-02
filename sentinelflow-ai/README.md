# SentinelFlow AI

Standalone AI-assisted cloud incident investigation project. Python standard library only.

See the [architecture diagram and explanation](ARCHITECTURE.md).

## Run

```sh
python agent.py --scenario database
python agent.py --scenario memory
python agent.py --scenario unknown
python agent.py --scenario database --model llama3.2:1b
python cloud_logs.py
python -m unittest -v
```

Open the report path printed by each command. Ollama must be running with the selected model installed for LLM analysis. No model is required for the rule-based fallback.

## Flow

Evidence -> hypothesis -> local Markdown runbook retrieval -> optional Ollama LLM -> validated cited recommendations -> HTML/JSON report and activity trace.

`rag.py` uses lexical retrieval, not embeddings. Add runbooks under `knowledge/`. A five-minute cache stores versioned built-in guidance; incident evidence is not cached. Invalid model output and connection failures fall back to rule-based guidance. Unknown/conflicting evidence suppresses model mitigation recommendations. Citation IDs are checked, but a person must verify their meaning and the proposed actions.

## CloudWatch

```sh
python cloud_logs.py --live --log-group /your/test/group --region ca-central-1 --profile YOUR_PROFILE --minutes 15
```

Requires AWS CLI authentication and scoped `logs:FilterLogEvents` permission. Reads at most 500 events; reports disclose truncation. No live AWS access has been validated. Start with non-sensitive test logs, which are saved locally in reports. Never commit credentials or reports containing sensitive information.

## MCP

Run `python mcp_server.py` through a compatible stdio MCP client. Configure the absolute Python executable and script path. Set OLLAMA_MODEL in the server environment if desired. Tools: search_runbooks and investigate_dummy_incident. Client registration is not automatic. Initialization/discovery/search were tested via subprocess; full interoperability is not certified.

## Scope

Local Llama 3.2 1B inference was demonstrated with synthetic evidence. No automatic remediation, continuous monitoring, Jira, or security attack-correlation detection is implemented. This project is independent of the sibling FileGuard project and does not import its code.
