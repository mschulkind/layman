# Build Logs & Diagnostics Resources

This directory contains guides and tools for diagnosing and accessing Cloudflare Workers build and runtime logs.

## Files

### 1. **BUILD_LOGS_GUIDE.md**
Comprehensive guide covering:
- Runtime logs (application logs)
  - Wrangler CLI: `wrangler tail` for real-time logs
  - Cloudflare Dashboard: Workers Logs
  - MCP tools: Query logs programmatically
- Build logs (deployment logs)
  - Local build output
  - Cloudflare Dashboard
  - Git integration logs
- Enabling Workers Logs
- Troubleshooting common build failures
- Quick command reference

### 2. **MCP_OBSERVABILITY_GUIDE.md**
Detailed guide for using the Cloudflare observability MCP:
- List workers and get worker details
- Discover available log fields
- Query worker logs as events or metrics
- Filter and calculation operators
- Example queries for common use cases
- Timeframe format reference
- Integration with jq for JSON processing

### 3. **scripts/diagnose-build.sh**
Automated diagnostic script that:
- Checks Node/npm/Wrangler versions
- Verifies build dependencies
- Runs local build and checks output
- Tests deployment with `--dry-run`
- Checks git status
- Provides next steps for troubleshooting

Usage:
```bash
./scripts/diagnose-build.sh
```

## Quick Start

### Check for Build Errors Locally
```bash
npm run build
```

### Test Deployment Without Uploading
```bash
npx wrangler deploy --dry-run
```

### View Real-time Worker Logs
```bash
npx wrangler tail layman
```

### Query Worker Logs via MCP
Use the `mcp_cloudflare-ob_query_worker_observability` tool in the Claude interface.

### Run Full Diagnostics
```bash
./scripts/diagnose-build.sh
```

## Methods to Access Logs

| Method | Use Case | Access |
|--------|----------|--------|
| **Local build** | Catch errors early | `npm run build` |
| **Dry-run deploy** | Test without uploading | `npx wrangler deploy --dry-run` |
| **Wrangler tail** | Real-time logs | `npx wrangler tail layman` |
| **Dashboard** | Visual interface | Cloudflare Dashboard → Workers & Pages |
| **MCP tools** | Programmatic access | Claude with Cloudflare observability MCP |
| **Diagnostic script** | Full health check | `./scripts/diagnose-build.sh` |

## Key Insights for Layman Project

The `layman` Worker is deployed as **static assets only** (no server-side code). This means:

- ✅ Can view deployment history in Cloudflare Dashboard
- ✅ Local build (`npm run build`) catches all errors
- ✅ Use `npx wrangler deploy --dry-run` to test before uploading
- ❌ `npx wrangler tail` doesn't work (no runtime logs for static assets)
- ✅ Check deployment status in Workers dashboard for errors

## Common Build Failure Causes

1. **Missing dependencies** - Run `npm install` and `npm run build` locally
2. **Invalid config** - Check `wrangler.toml` syntax and file references
3. **Build script errors** - Run build locally: `npm run build`
4. **Incompatible Node version** - Check `package.json` engines
5. **Git integration issues** - Check GitHub/GitLab webhooks and permissions

## Next Steps If Deployment Fails

1. Run: `./scripts/diagnose-build.sh`
2. Check Cloudflare Dashboard for deployment details
3. Review local build output: `npm run build`
4. Test with: `npx wrangler deploy --dry-run`
5. Check git integration if using GitHub/GitLab
6. View build logs in dashboard Deployments page
