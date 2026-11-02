# Database connection exhaustion
Signals: too many connections, connection pool exhausted, high database connections, checkout connection timeout.
Check: inspect active sessions, application pool configuration, recent deploys, connection leaks and query duration.
Mitigation: ask the incident lead to approve rollback of a correlated deployment or adjustment of pool limits after checking database capacity. Do not increase limits blindly or terminate sessions without review.
Verification: confirm connection usage and failed requests return to baseline and watch for recurrence.
