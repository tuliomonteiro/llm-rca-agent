# Incident INC-002: report-worker OOMKilled — 2024-04-02

## Summary
report-worker pods were OOMKilled repeatedly for 40 minutes causing a backlog of 1,200 pending reports.

## Timeline
- 09:10 UTC — Product team triggered bulk report export for 50,000 users
- 09:14 UTC — First OOMKill observed on report-worker-0
- 09:15 UTC — Kubernetes restarted pod; it OOMKilled again within 60 seconds
- 09:18 UTC — All 3 worker replicas were crash-looping
- 09:45 UTC — Engineering increased memory limit from 512Mi to 2Gi
- 09:50 UTC — Workers stabilized, backlog processing began
- 10:30 UTC — All reports completed

## Root Cause
report-worker loaded entire user datasets into memory before processing. A 50,000-user export required ~1.8GB of RAM, far exceeding the 512Mi limit.

## Contributing Factors
- No pagination or streaming in the report generation code
- Memory limit was set in 2022 and never reviewed after user base growth
- No alerting on large export job initiation

## Prevention Actions Taken
- Refactored report generation to stream data in 500-row batches
- Memory limit raised to 2Gi with autoscaling enabled
- Added pre-flight check: jobs > 10,000 rows are queued as chunked sub-jobs
- Added Slack notification when export > 5,000 rows is triggered
