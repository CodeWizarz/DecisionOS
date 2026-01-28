# DecisionOS Operational Runbook

This document provides guidelines for maintaining, troubleshooting, and operating DecisionOS in production.

## System Monitoring

### Key Metrics to Watch

1.  **API Latency**:
    - *Target*: < 200ms p95.
    - *Alert*: > 500ms for 5 minutes.
    - *Source*: Structlog output / Application Performance Monitor (APM).

2.  **Queue Lag**:
    - *Target*: < 100 jobs pending.
    - *Alert*: > 1000 jobs or task age > 10 minutes.
    - *Source*: Redis metrics (List length).

3.  **Worker Error Rate**:
    - *Alert*: > 5% failure rate.
    - *Source*: Log patterns `level=error`.

### Logging

Logs are output in JSON format in production (when `ENV=production`).
- **Trace ID**: Look for `request_id` or `correlation_id` to trace a request across API and Worker logs.
- **Levels**: 
    - `INFO`: Normal operations (decisions generated).
    - `WARNING`: Anomaly flags or degraded performance (e.g., automated fallback).
    - `ERROR`: System failures (DB connection lost, unhandled exceptions).

## Troubleshooting

### Incident: Decisions Stuck in "Processing"
**Symptoms**: users querying `/decisions/{id}` see `status: processing` indefinitely.

**Investigation Steps**:
1. Check Queue Depth: Is the worker keeping up?
2. Check Worker Logs: Are tasks failing silently?
3. Check Redis Connection: Is the broker reachable?

**Recovery**:
- Restart worker containers: `docker-compose restart worker`
- If queue is poisoned with bad jobs, purge Redis (Data loss risk!): `redis-cli FLUSHDB` (Last resort).

### Incident: High Anomaly Rate
**Symptoms**: Many decisions flagged as `needs_review`.

**Investigation**:
- Check input data distribution. Is there a genuine market shift?
- Verify `SignalEngine` logic.
- Check `GOVERNANCE_POLICY` thresholds.

## Maintenance Tasks

### Database Migrations
Always backup database before upgrading.
```bash
# Check current revision
alembic current

# Apply pending migrations
alembic upgrade head
```

### Data Pruning
Old operational data (metrics, logs) should be rotated out every 90 days.
*(Automated task implementation pending in `app/workers/tasks.py`)*

## Support Contacts
- **DevOps**: devops@decisionos.internal
- **On-Call**: Page "DecisionOS Primary" policy.
