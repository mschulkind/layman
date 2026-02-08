#!/usr/bin/env bash
# Build diagnostics script for layman
# Usage: ./scripts/diagnose-build.sh

set -e

echo "=== Layman Build Diagnostics ==="
echo ""

# Check Node/npm versions
echo "1. Checking Node/npm versions..."
node --version
npm --version
echo ""

# Check wrangler version
echo "2. Checking Wrangler version..."
npx wrangler --version
echo ""

# Check build dependencies
echo "3. Checking build dependencies..."
npm ls --depth=0 | head -20
echo ""

# Run build locally
echo "4. Running local build..."
if npm run build; then
    echo "✅ Build succeeded locally"
else
    echo "❌ Build failed locally - errors shown above"
    exit 1
fi
echo ""

# Check build output
echo "5. Checking build output..."
if [ -d "site/dist" ]; then
    echo "✅ Build output directory exists"
    ls -lah site/dist/ | head -10
else
    echo "❌ No build output directory"
    exit 1
fi
echo ""

# Test deployment (dry-run)
echo "6. Testing deployment (dry-run)..."
cd site
if npx wrangler deploy --dry-run; then
    echo "✅ Deployment test passed"
else
    echo "❌ Deployment test failed"
    exit 1
fi
cd ..
echo ""

# Check git status
echo "7. Checking git status..."
if git status --porcelain | head -10; then
    echo "✅ Git status retrieved"
else
    echo "⚠️  Git status check failed"
fi
echo ""

echo "=== Diagnostics Complete ==="
echo ""
echo "Next steps if deployment fails:"
echo "1. Check Cloudflare dashboard: https://dash.cloudflare.com/?to=/:account/workers-and-pages"
echo "2. View recent deployments and their build logs"
echo "3. For runtime errors, use: npx wrangler tail layman"
echo "4. Check wrangler logs: cat ~/.config/.wrangler/logs/wrangler-*.log"
