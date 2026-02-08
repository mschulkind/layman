# Using Cloudflare MCP to Access Worker Logs Programmatically

This guide shows how to use the Cloudflare observability MCP to access worker logs without relying on the dashboard.

## 1. List Available Workers

Use the MCP to list all workers in your account:

```
mcp_cloudflare-ob_workers_list
```

Returns all workers with their names, descriptions, and statuses.

## 2. Get Worker Details

Get detailed information about a specific worker:

```
mcp_cloudflare-ob_workers_get_worker scriptName="layman"
```

Returns worker configuration, bindings, limits, etc.

## 3. Find Available Log Fields

Before querying logs, discover what fields are available:

```
mcp_cloudflare-ob_observability_keys
  keysQuery:
    timeframe:
      reference: "2025-02-08T00:00:00Z"
      offset: "-1d"
    limit: 100
```

Common fields returned:
- `$metadata.service` - Worker name
- `$metadata.origin` - Request type (fetch, scheduled, etc.)
- `$metadata.trigger` - Route/trigger details
- `$metadata.message` - Log messages
- `$metadata.error` - Error messages
- `$metadata.level` - Log level (info, error, warn)
- `$metadata.requestId` - Unique request ID

## 4. Get Values for a Specific Field

Find all distinct values for a field:

```
mcp_cloudflare-ob_observability_values
  valuesQuery:
    timeframe:
      reference: "2025-02-08T00:00:00Z"
      offset: "-1h"
    key: "$metadata.service"
    type: "string"
    limit: 50
```

## 5. Query Worker Logs (Events View)

Get recent log events as a list:

```
mcp_cloudflare-ob_query_worker_observability
  query:
    queryId: "workers-logs-events"
    view: "events"
    limit: 10
    parameters:
      datasets: ["cloudflare-workers"]
      filters:
        - key: "$metadata.service"
          operation: "eq"
          type: "string"
          value: "layman"
        - key: "$metadata.level"
          operation: "eq"
          type: "string"
          value: "error"
    timeframe:
      reference: "2025-02-08T00:00:00Z"
      offset: "-24h"
```

## 6. Query Worker Logs (Calculations View)

Get aggregated metrics:

```
mcp_cloudflare-ob_query_worker_observability
  query:
    queryId: "workers-logs-metrics"
    view: "calculations"
    parameters:
      datasets: ["cloudflare-workers"]
      filters:
        - key: "$metadata.service"
          operation: "eq"
          type: "string"
          value: "layman"
      calculations:
        - operator: "count"
          alias: "request_count"
        - operator: "p99"
          key: "CPUTime"
          keyType: "number"
          alias: "p99_cpu_time"
      groupBys:
        - value: "$metadata.level"
          type: "string"
    timeframe:
      reference: "2025-02-08T00:00:00Z"
      offset: "-24h"
```

## 7. Filter Operators

When querying, use these filter operations:

- `eq` - equals
- `neq` - not equals
- `gt` - greater than
- `gte` - greater than or equal
- `lt` - less than
- `lte` - less than or equal
- `includes` - contains substring (case-insensitive)
- `not_includes` - doesn't contain substring
- `starts_with` - begins with
- `regex` - regex pattern matching (RE2 syntax, no lookaheads)
- `exists` - field is not null
- `is_null` - field is null
- `in` - value in list
- `not_in` - value not in list

## 8. Calculation Operators

For aggregated metrics:

- `count` - total count
- `uniq` - distinct count
- `sum` - total sum
- `avg` - average
- `min` - minimum
- `max` - maximum
- `median` - median value
- `stddev` - standard deviation
- `variance` - variance
- `p001`, `p01`, `p05`, `p10`, `p25`, `p75`, `p90`, `p95`, `p99`, `p999` - percentiles

## 9. Example Queries

### Get all errors in last hour
```
filters:
  - key: "$metadata.service"
    operation: "eq"
    type: "string"
    value: "layman"
  - key: "$metadata.error"
    operation: "exists"
    type: "boolean"
timeframe:
  reference: "2025-02-08T17:00:00Z"
  offset: "-1h"
```

### Find requests taking over 1 second
```
filters:
  - key: "CPUTime"
    operation: "gt"
    type: "number"
    value: 1000
```

### Count requests by status code
```
groupBys:
  - value: "event.response.status"
    type: "string"
calculations:
  - operator: "count"
    alias: "count"
```

### P99 latency by path
```
groupBys:
  - value: "event.request.url"
    type: "string"
calculations:
  - operator: "p99"
    key: "CPUTime"
    keyType: "number"
    alias: "p99_latency"
```

## 10. Timeframe Formats

### Absolute (specific dates)
```
timeframe:
  from: "2025-02-07T00:00:00Z"
  to: "2025-02-08T23:59:59Z"
```

### Relative (offset from a reference time)
```
timeframe:
  reference: "2025-02-08T17:00:00Z"
  offset: "-1h"          # last 1 hour
  offset: "-24h"         # last 24 hours
  offset: "-7d"          # last 7 days
  offset: "+30m"         # next 30 minutes (rarely used)
  offset: "-6h20m"       # last 6 hours 20 minutes
```

## 11. Integration with jq

Pipe results through `jq` for JSON processing (if using wrangler):

```bash
npx wrangler tail layman | jq '.event.request.url'
```

## 12. Troubleshooting

**"No results found"**
- Broaden the timeframe
- Check that the service name is correct
- Verify the filter values match available data

**"Field doesn't exist"**
- Use `observability_keys` to verify available fields
- Check field name spelling (case-sensitive)

**"Invalid regex"**
- Use RE2 syntax (not PCRE/JavaScript)
- No lookaheads/lookbehinds allowed
- Example valid patterns: `^5\d{2}$`, `\bERROR\b`

## Reference

- Cloudflare Observability Docs: https://developers.cloudflare.com/workers/observability/
- RE2 Regex Syntax: https://github.com/google/re2/wiki/Syntax
