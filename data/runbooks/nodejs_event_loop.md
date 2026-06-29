# Runbook: Node.js Event Loop Blocking & Server Unresponsiveness

## Overview

Node.js runs on a single-threaded event loop. Any synchronous CPU-intensive work, or a blocking I/O call that doesn't yield, will block ALL other callbacks — including health check endpoints, incoming HTTP requests, and timers — until that work completes. This is the most common reason a Node.js health check times out even though it does nothing with the database.

## Symptoms

- Health check endpoint (`/health`, `/ping`, `/status`) times out or returns very slowly after a heavy endpoint was called
- High CPU usage on the Node.js process
- All endpoints become slow or unresponsive simultaneously, not just the DB-related ones
- Logs stop emitting (even log writes are queued behind the event loop)
- `libuv` thread pool exhaustion: DB queries, file I/O, crypto operations pile up
- Memory may stay normal (distinguishes this from OOM)
- No database errors — the DB itself is healthy

## Common Root Causes

### 1. Synchronous / CPU-bound computation in a request handler
- Large JSON.parse() or JSON.stringify() on multi-MB payloads
- Synchronous crypto (bcrypt with high rounds, synchronous hashing)
- In-process sorting, filtering, or aggregation over large datasets
- Regex with catastrophic backtracking
- `fs.readFileSync` / `fs.writeFileSync` in a request path

### 2. Unresolved or very long async chain
- `await` on a promise that never resolves (missing timeout)
- Database query with no query timeout that runs for minutes
- External HTTP call with no timeout that hangs

### 3. libuv thread pool exhaustion (pool_size = 4 by default)
- Too many concurrent `fs`, `crypto`, `dns`, or native add-on calls queued
- One slow DB query can block the thread pool and delay all other async I/O

### 4. Memory pressure causing GC pauses
- Stop-the-world GC pauses can freeze the event loop for hundreds of milliseconds
- Large heap allocations from parsing / building big objects

## Diagnosis

### Check if the event loop is blocked
```bash
# Watch CPU: if node process is pegged at ~100% on one core, event loop is blocked
top -p $(pgrep node)

# Or with pidstat
pidstat -u -p $(pgrep node) 1
```

### Measure event loop lag
Add this to your app (or check your APM):
```js
let last = Date.now()
setInterval(() => {
  const lag = Date.now() - last - 1000
  if (lag > 100) console.warn(`Event loop lag: ${lag}ms`)
  last = Date.now()
}, 1000)
```

### Profile what's blocking
```bash
# Run with built-in profiler
node --prof server.js

# After reproducing the issue, process the log
node --prof-process isolate-*.log | head -50
```

### Check libuv thread pool
```bash
# Default is 4; increase if you have many concurrent async native calls
UV_THREADPOOL_SIZE=16 node server.js
```

### Identify slow endpoints
```bash
# Check response times in access logs
grep "POST /api/heavy-endpoint" access.log | awk '{print $NF}' | sort -n | tail -10
```

## Immediate Actions

1. **Restart the Node.js process** to restore responsiveness immediately
   ```bash
   pm2 restart app
   # or
   kubectl rollout restart deployment/node-app
   ```

2. **Identify the offending request** in logs — look for requests to the heavy endpoint that started just before the health check began timing out

3. **Temporarily rate-limit or disable** the heavy endpoint if it's causing cascading unresponsiveness

4. **Increase UV_THREADPOOL_SIZE** if the bottleneck is async I/O saturation:
   ```bash
   UV_THREADPOOL_SIZE=16 node server.js
   ```

5. **Check active handles and requests**:
   ```bash
   # In a REPL or debug session
   process._getActiveHandles().length
   process._getActiveRequests().length
   ```

## Prevention

### Move CPU work off the event loop
```js
// Option 1: worker_threads for CPU-bound tasks
const { Worker } = require('worker_threads')

// Option 2: child_process for isolation
const { fork } = require('child_process')

// Option 3: Break work into chunks with setImmediate
async function processInChunks(items) {
  for (let i = 0; i < items.length; i++) {
    processItem(items[i])
    if (i % 100 === 0) await new Promise(r => setImmediate(r)) // yield
  }
}
```

### Always set timeouts on async operations
```js
// Database query timeout
await db.query('SELECT ...', { timeout: 5000 })

// HTTP call timeout
const controller = new AbortController()
setTimeout(() => controller.abort(), 5000)
await fetch(url, { signal: controller.signal })
```

### Stream large payloads instead of buffering
```js
// Bad: reads entire body into memory before parsing
app.post('/upload', express.json({ limit: '50mb' }), handler)

// Better: stream and process incrementally
app.post('/upload', (req, res) => {
  const stream = JSONStream.parse('*')
  req.pipe(stream)
  stream.on('data', chunk => processChunk(chunk))
})
```

### Add health check timeout monitoring
```js
// Health check should always respond in < 200ms
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() })
})
// Alert if p99 of /health > 500ms — it means something else is blocking the loop
```

### Increase UV_THREADPOOL_SIZE for I/O-heavy apps
```bash
# In your start script or environment
UV_THREADPOOL_SIZE=16 node server.js
```

## Related Incidents

- Health check timeouts after JSON parsing of large payloads → synchronous JSON.parse blocking event loop
- All endpoints slow after bcrypt login → bcrypt.hashSync() called instead of bcrypt.hash()
- Intermittent 503s under load → libuv thread pool exhausted by concurrent DB queries with no timeout
