# Container memory pressure
Signals: OOMKilled, out of memory, container restarts, high memory utilization.
Check: inspect container termination reason, memory trend, limits and recent deployment changes.
Mitigation: ask the incident lead to approve rollback of a correlated deployment or a capacity adjustment after checking available resources. Restarting alone may hide a leak.
Verification: confirm memory stabilizes, restarts stop and application health returns to baseline.
