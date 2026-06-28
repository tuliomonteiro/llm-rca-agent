# Runbook: High Memory Usage / OOM Kills

## Symptoms
- Pods restarting with OOMKilled exit code
- Memory usage trending upward without leveling off (memory leak)
- Service degradation before crash

## Immediate Actions
1. Check pod memory: `kubectl top pods -n <namespace>`
2. Describe the pod for OOM events: `kubectl describe pod <pod-name>`
3. Increase memory limit temporarily as a hotfix: edit the deployment resource limits
4. Roll back the most recent deployment if spike coincides with a release

## Root Causes
- Memory leak in application (unbounded caches, event listeners not cleaned up)
- Sudden traffic spike with insufficient limits
- Large payloads being held in memory (streaming not used)
- Third-party library with known memory leak

## Prevention
- Set memory requests AND limits; never leave limits unset
- Configure Horizontal Pod Autoscaler (HPA) to scale before OOM
- Add heap profiling in staging with tools like py-spy or async-profiler
- Alert at 80% memory utilization, not after OOM
