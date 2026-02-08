# Cloudflare Workers Logging & Diagnostics

> Research and documentation on accessing Cloudflare Workers build logs and runtime logs via multiple methods, including MCPs.

## 📚 Documentation Files

Start here based on your needs:

### For Quick Reference
- **[LOGS_AND_DIAGNOSTICS.md](./LOGS_AND_DIAGNOSTICS.md)** ← START HERE
  - Quick overview of all methods
  - Command reference
  - Troubleshooting checklist

### For Comprehensive Guides  
- **[BUILD_LOGS_GUIDE.md](./BUILD_LOGS_GUIDE.md)**
  - Complete guide to all logging methods
  - Runtime logs (wrangler tail, dashboard, MCP)
  - Build logs (local, dry-run, dashboard)
  - Enabling Workers Logs
  - Best practices

- **[MCP_OBSERVABILITY_GUIDE.md](./MCP_OBSERVABILITY_GUIDE.md)**
  - Reference for Cloudflare observability MCP
  - How to query logs programmatically
  - Filter and calculation operators
  - Example queries
  - Timeframe format reference

### For Automation
- **[scripts/diagnose-build.sh](./scripts/diagnose-build.sh)**
  - Automated diagnostic script
  - Checks versions, builds, tests deployment
  - Provides troubleshooting next steps
  - Run: `./scripts/diagnose-build.sh`

## 🎯 Quick Start

### Check for Build Errors
```bash
npm run build
```

### Test Deployment
```bash
npx wrangler deploy --dry-run
```

### View Runtime Logs (real-time)
```bash
npx wrangler tail layman
```

### View Logs via MCP
Use Claude with these MCPs:
- `mcp_cloudflare-ob_query_worker_observability` - query logs
- `mcp_cloudflare-ob_observability_keys` - see available fields
- `mcp_cloudflare-ob_observability_values` - see values for a field

### Run Full Diagnostics
```bash
./scripts/diagnose-build.sh
```

## 🔍 Methods Available

| Method | Purpose | Command/Access |
|--------|---------|-----------------|
| **Local build** | Catch errors early | `npm run build` |
| **Dry-run** | Test before uploading | `npx wrangler deploy --dry-run` |
| **Wrangler tail** | Real-time logs | `npx wrangler tail layman` |
| **Dashboard** | Visual interface | Cloudflare Dashboard → Workers & Pages |
| **MCP tools** | Programmatic access | Claude with observability MCP |
| **Diagnostic script** | Full health check | `./scripts/diagnose-build.sh` |

## 📊 Key Resources Used

This research was conducted using:

1. **Web Search** (Tavily MCP)
   - Searched: "Cloudflare Workers build logs deployment logs CLI wrangler"
   - Found: Official docs, GitHub issues, community posts

2. **Cloudflare Documentation** (MCP)
   - Searched: "build logs deployment logs diagnostics CLI wrangler"
   - Found: Comprehensive guides on logging, debugging, troubleshooting

3. **CLI Testing**
   - Tested: `npm run build`, `npx wrangler deploy --dry-run`, `npx wrangler tail`
   - Verified: Methods work as documented

## ✨ Key Findings

### Runtime Logs
- ✅ **Wrangler tail** - Real-time streaming via CLI
- ✅ **Dashboard** - Historical logs with query builder
- ✅ **MCP** - Programmatic access to logs

### Build Logs  
- ✅ **Local build** - Most reliable for catching errors
- ✅ **Dry-run** - Test without uploading
- ✅ **Dashboard** - View deployment history and logs
- ✅ **Wrangler logs** - Debug logs in `~/.config/.wrangler/logs/`

### For Layman Project
- The Worker is **static assets only** (no server code)
- `wrangler tail` won't work (no runtime logs)
- But `npm run build` and Dashboard logs will work

## 🎓 How to Use MCPs for Diagnostics

### Example 1: Get all errors in last hour
```
mcp_cloudflare-ob_query_worker_observability
  view: "events"
  parameters:
    filters:
      - key: "$metadata.service"
        operation: "eq"
        type: "string"
        value: "layman"
      - key: "$metadata.error"
        operation: "exists"
        type: "boolean"
    timeframe:
      offset: "-1h"
```

### Example 2: P99 latency by status code
```
mcp_cloudflare-ob_query_worker_observability
  view: "calculations"
  parameters:
    filters:
      - key: "$metadata.service"
        operation: "eq"
        type: "string"
        value: "layman"
    calculations:
      - operator: "p99"
        key: "CPUTime"
        keyType: "number"
        alias: "p99_latency"
    groupBys:
      - value: "event.response.status"
        type: "string"
```

## 🚀 Future Improvements

Now that these methods are documented, you can:

1. **Diagnose autonomously** - No need for user copy/paste
2. **Automate monitoring** - Script checks via CI/CD
3. **Create alerts** - Query logs for specific errors
4. **Build dashboards** - Aggregate metrics from MCP
5. **Historical analysis** - Query past deployments

## 📋 Related Documentation

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Reference](https://developers.cloudflare.com/workers/wrangler/commands/)
- [Workers Observability](https://developers.cloudflare.com/workers/observability/)
- [Real-time Logs](https://developers.cloudflare.com/workers/observability/logs/real-time-logs/)
- [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)

---

**Created:** February 8, 2026
**Research via:** Tavily web search, Cloudflare docs MCP, Wrangler CLI testing
