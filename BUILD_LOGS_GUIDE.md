# Cloudflare Workers Build Logs - Access Methods

## Runtime Logs (Application Logs)

### 1. **Wrangler CLI: `wrangler tail` (Real-time Logs)**
View live request logs and exceptions as they happen.

**Note:** `wrangler tail` works for Workers with server-side code. The `layman` Worker is static assets only, so it won't have runtime logs. For workers with code execution:

```bash
# Basic usage
npx wrangler tail layman

# Filter by status (ok, error, canceled)
npx wrangler tail layman --status error

# Filter by HTTP method
npx wrangler tail layman --method POST

# Filter by search text (in console.log messages)
npx wrangler tail layman --search "error"

# Filter by IP address
npx wrangler tail layman --ip "self"

# Pipe to jq for JSON filtering
npx wrangler tail layman | jq '.event.request.url'
```

**Output format:** Structured JSON objects with:
- `outcome` - "ok" or error status
- `logs` - console.log messages
- `exceptions` - uncaught errors
- `event.request` - request details (URL, method, headers)
- `event.response` - response status

### 2. **Cloudflare Dashboard: Workers Logs**
View historical logs stored in your Cloudflare account.

1. Go to **Cloudflare Dashboard** → **Workers & Pages**
2. Select your **Worker** (e.g., "layman")
3. Select **Observability** → **Workers Logs** or **Logs** → **Live**

Features:
- Query builder for advanced filtering
- View by Events (timestamp order) or Invocations (grouped by request)
- Metrics like p99 latency, error rates, etc.

### 3. **Workers Logs (via MCP)**
Query workers logs programmatically using the Cloudflare observability MCP:

```bash
# List available keys in logs
mcp_cloudflare-ob_observability_keys

# Get values for a specific key
mcp_cloudflare-ob_observability_values key="$metadata.service"

# Query logs for specific events
mcp_cloudflare-ob_query_worker_observability \
  view="events" \
  filters=[{"key": "$metadata.service", "operation": "eq", "value": "layman"}]

# Calculate metrics
mcp_cloudflare-ob_query_worker_observability \
  view="calculations" \
  calculations=[{"operator": "count"}]
```

## Build Logs (Deployment Build Logs)

### **Local Build Output**
The most accessible method - run the build locally to see errors:

```bash
# Build the site (produces build errors)
npm run build

# Deploy with verbose output
npx wrangler deploy --verbose

# Dry-run deployment to test without uploading
npx wrangler deploy --dry-run
```

### **Cloudflare Dashboard**
Check deployment history and build errors:

1. **Cloudflare Dashboard** → **Workers & Pages**
2. Select your **Worker**
3. Go to **Deployments** or **Settings** → **Git Integration**
4. View deployment status and error messages
5. For Pages: check **Build Logs** tab per deployment

### **Git Integration Issues**
If using GitHub/GitLab, check:

1. **Cloudflare Dashboard** → **Pages Project** → **Deployments**
2. Look for error banners indicating:
   - Repository permission issues
   - Account conflicts
   - Build process failures
3. Click on failed deployment to see build logs

## Enable Workers Logs (Persistent Logging)

To enable persistent logging for your Worker (default for new Workers):

**wrangler.toml:**
```toml
[observability]
enabled = true
head_sampling_rate = 1  # 1 = 100%, 0.1 = 10%, etc.
```

**wrangler.jsonc:**
```json
{
  "observability": {
    "enabled": true,
    "head_sampling_rate": 1
  }
}
```

Then redeploy:
```bash
npx wrangler deploy
```

## Troubleshooting Build Failures

### Common Issues

1. **"No event handlers were registered. This script does nothing."**
   - Check `dir` and `main` config in wrangler.toml
   - Ensure file extension is `.mjs` (not `.js`) if using ES modules

2. **Build succeeds locally but fails on Cloudflare**
   - Check `npx wrangler deploy --dry-run` output
   - Verify all dependencies are in `package.json`
   - Check for environment-specific issues (Windows vs Linux paths)

3. **Pages Functions bundle too large**
   - Minify code: `npx wrangler pages functions build --minify`
   - Check build output size limits (default: varies by plan)

4. **Git integration fails**
   - Check GitHub/GitLab repository permissions
   - Verify repository isn't used across multiple Cloudflare accounts
   - Check SCM installation warnings in dashboard

## Quick Command Reference

```bash
# View real-time logs
npx wrangler tail layman

# View Pages Function logs
npx wrangler pages deployment tail --project-name my-project

# Build locally to catch errors early
npm run build

# Test deployment without uploading
npx wrangler deploy --dry-run

# Deploy with all verbose output
npx wrangler deploy --verbose

# View specific deployment logs
npx wrangler pages deployment tail [DEPLOYMENT_ID]
```

## Best Practices

1. **Always run locally first:** `npm run build` catches most errors early
2. **Use `--dry-run`:** Test the deployment without uploading
3. **Enable Workers Logs:** Store logs for historical analysis
4. **Monitor in real-time:** Use `wrangler tail` after deployment
5. **Check git integration:** Verify GitHub/GitLab webhooks are enabled
6. **Use structured logging:** Log JSON objects for better queryability
