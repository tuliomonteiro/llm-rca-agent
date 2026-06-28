# Runbook: Database Connection Pool Exhaustion

## Symptoms
- Services returning 503 or 500 errors
- Logs showing "connection pool exhausted", "too many connections", or "ECONNREFUSED"
- Increased latency followed by complete failure

## Immediate Actions
1. Check active connections: `SELECT count(*) FROM pg_stat_activity;`
2. Identify long-running queries: `SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;`
3. Kill idle connections if needed: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';`
4. Restart the affected service pod to release held connections

## Root Causes
- Missing connection.close() calls in application code (connection leak)
- Traffic spike exceeding pool_size configuration
- Slow queries holding connections open
- Database failover causing connection re-establishment storm

## Prevention
- Set pool_size based on expected concurrency * 1.5
- Enable connection timeouts (connection_timeout=30s)
- Use pgBouncer as a connection pooler in front of PostgreSQL
- Add connection pool metrics to your observability stack
