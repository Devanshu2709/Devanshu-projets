# Uncertain or conflicting evidence
Signals: ambiguous timeout, conflicting signals, empty logs, unknown cause.
Check: collect recent deployment history, upstream health, application logs and resource metrics for the same time window. A timeout alone does not prove database failure.
Mitigation: escalate to the service owner when evidence is missing or conflicting. Gather evidence before proposing configuration changes.
Verification: validate hypotheses against independent metrics. Do not claim root cause or resolution without confirmation.
