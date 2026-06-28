# Incident INC-001: auth-api 503 Errors — 2024-03-15

## Summary
auth-api service returned HTTP 503 for all requests for 11 minutes between 14:22 and 14:33 UTC.
Approximately 8,400 authentication requests failed. No user data was lost.

## Timeline
- 14:20 UTC — Deployment of auth-api v2.4.1 completed
- 14:22 UTC — Error rate jumped from 0.1% to 100% on auth-api
- 14:25 UTC — On-call engineer paged via PagerDuty
- 14:28 UTC — Engineer identified PostgreSQL connection errors in logs
- 14:31 UTC — Rolled back to v2.4.0
- 14:33 UTC — Error rate returned to baseline

## Root Cause
The v2.4.1 release introduced a new background job that opened database connections but never closed them due to a missing `finally` block. Under normal load the pool was exhausted within 2 minutes of deployment.

## Contributing Factors
- No connection leak detection in staging environment
- Pool size of 10 was too small for the combined load of API + background jobs
- Alert threshold was set to 5 minutes; outage was 11 minutes before auto-remediation

## Prevention Actions Taken
- Added `finally: conn.close()` in the background job
- Increased pool_size from 10 to 25
- Added connection pool utilization alert at 70% threshold
- Added connection leak test to staging CI pipeline
