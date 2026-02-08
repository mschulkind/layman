# Website & Interactive Demo

The Layman website is an Astro static site that includes a landing page,
an interactive demo, and a custom 404 page. Astro handles the build pipeline,
giving us content-hashed filenames for cache busting and a clean deployment
to Cloudflare Pages.

**Live site:** <https://layman.mschulkind.workers.dev/>  
**Live demo:** <https://layman.mschulkind.workers.dev/demo/>

## Running Locally

### First-time setup

```bash
just setup-demo
```

This installs npm dependencies and the Playwright Chromium browser.

### Dev server (hot reload)

```bash
just site-dev
```

Opens on `http://localhost:4321/`. The landing page is at `/`, the demo at
`/demo/`. Changes to source files are reflected instantly.

### Production preview

```bash
just site-preview
```

Builds the entire site and serves it from `http://localhost:4321/` — exactly
how it will look when deployed.

## Deployment

The site is deployed to Cloudflare Workers as a static assets Worker.

### How it works

1. Run `just site-deploy` (or `cd site && npm run deploy`).
2. Astro builds the landing page, demo, and 404 page into `site/dist/`.
3. All JS/CSS assets get content-hashed filenames (e.g.,
   `_astro/App.Bojvjspf.js`) for aggressive caching.
4. Wrangler uploads the `dist/` directory as static assets to the
   `layman` Worker (configured in `site/wrangler.jsonc`).
5. The Worker serves `404.html` for unknown routes via
   `not_found_handling: "404-page"`.

**Live URL:** <https://layman.mschulkind.workers.dev/>

### Build for deployment

```bash
just site-build
```

Output lands in `site/dist/`.

### Deploy

```bash
just site-deploy       # Build + deploy to Workers
just site-deploy-dry   # Validate without publishing
```

## Project Structure

```text
site/
├── astro.config.mjs         # Astro configuration (React integration, Tailwind)
├── wrangler.jsonc            # Cloudflare Workers deployment config
├── package.json              # Unified dependencies
├── tsconfig.json
├── vitest.config.ts          # Unit test configuration
├── playwright.config.ts      # E2E test configuration
├── eslint.config.mjs
├── e2e/                      # Playwright E2E tests
│   ├── demo.spec.ts          # Demo E2E tests (18 tests)
│   └── site.spec.ts          # Landing page + 404 E2E tests (9 tests)
├── src/
│   ├── pages/
│   │   ├── index.astro       # Landing page (/)
│   │   ├── 404.astro         # Custom 404 page
│   │   └── demo/
│   │       └── index.astro   # Demo page wrapper (/demo/)
│   └── demo/                 # React demo source code
│       ├── App.tsx
│       ├── main.tsx
│       ├── index.css
│       ├── components/       # React UI components
│       │   ├── DemoContainer.tsx
│       │   ├── HelpOverlay.tsx
│       │   ├── LayoutSwitcher.tsx
│       │   ├── StatusBar.tsx
│       │   └── Window.tsx
│       ├── hooks/
│       │   └── use-keyboard.ts
│       ├── layouts/           # Pure layout engine (no React)
│       │   ├── autotiling.ts
│       │   ├── grid.ts
│       │   ├── master-stack.ts
│       │   ├── three-column.ts
│       │   ├── types.ts
│       │   └── index.ts
│       ├── store/
│       │   └── window-store.ts
│       └── test/
│           └── setup.ts
└── dist/                     # Build output (gitignored)
```

### How the demo works with Astro

The demo is a React SPA that runs entirely client-side. The Astro page at
`src/pages/demo/index.astro` renders the React `<App />` component with the
`client:only="react"` directive, meaning:

- No server-side rendering — the React app mounts in the browser
- Astro handles the HTML shell, asset fingerprinting, and build pipeline
- The React code lives in `src/demo/` and imports are all relative

### Architecture layers

| Layer | Purpose |
|-------|---------|
| **Layouts** (`src/demo/layouts/`) | Pure functions that compute window positions from a list of windows + container rect. Zero React dependencies. |
| **Store** (`src/demo/store/`) | Zustand store managing windows, focus, layout selection, and all user actions. |
| **Hooks** (`src/demo/hooks/`) | `useKeyboard` maps keyboard events to store actions. |
| **Components** (`src/demo/components/`) | React components rendering the virtual desktop. Framer Motion handles layout animations. |

## Tech Stack

- **Astro 5** — static site framework with asset fingerprinting
- **React 19** — UI framework (demo runs as a `client:only` island)
- **TypeScript** — type safety
- **Tailwind CSS v4** — styling (via `@tailwindcss/vite`)
- **Zustand** — state management
- **Framer Motion** — layout animations
- **Wrangler 4** — Cloudflare Workers deployment
- **Vitest** — unit tests (jsdom)
- **Playwright** — E2E browser tests

## Testing

### Unit tests (Vitest)

```bash
just demo-test        # Run once
just demo-test-cov    # Run with coverage report
```

Unit tests cover the layout engine, Zustand store, React components, and
keyboard hook. 97 tests across 12 test files.

### E2E browser tests (Playwright)

```bash
just demo-test-e2e          # Headless (CI-friendly)
just demo-test-e2e-headed   # Visible browser (debugging)
```

Playwright tests build the full Astro site, start a preview server, and
drive a real Chromium browser. They verify:

**Demo tests** (18 tests):
- Page loads with correct initial state
- Keyboard shortcuts spawn/close/focus windows
- Layout switcher buttons work
- Help overlay opens and closes
- Focus navigation cycles through windows
- Full spawn → switch → navigate → close workflow

**Landing page tests** (6 tests):
- Hero section renders correctly
- Features section displays
- Layout showcase tabs work
- Demo link is present

**404 page tests** (3 tests):
- Shows 404 for unknown routes
- Links back to home and demo

### Run everything

```bash
just site-check   # Lint + unit tests + E2E tests
```

This is also included in the top-level `just check`.

## Keyboard Shortcuts (Demo)

| Key | Action |
|-----|--------|
| `N` | Spawn a new window |
| `Q` | Close the focused window |
| `H` / `←` | Focus previous window |
| `L` / `→` | Focus next window |
| `J` / `↓` | Focus next window |
| `K` / `↑` | Focus previous window |
| `Shift+K` | Move window up in stack |
| `Shift+J` | Move window down in stack |
| `Enter` | Swap focused window with master |
| `1` | Switch to MasterStack layout |
| `2` | Switch to Autotiling layout |
| `3` | Switch to Grid layout |
| `4` | Switch to ThreeColumn layout |
| `?` | Toggle keyboard shortcut help |

## Available Layouts

- **MasterStack** — One master window + vertical stack on the right
- **Autotiling** — Alternating horizontal/vertical splits (spiral pattern)
- **Grid** — Even grid distribution (cols = ceil(sqrt(n)))
- **ThreeColumn** — Center master with balanced left/right stacks

## Just Commands Reference

| Command | Description |
|---------|-------------|
| `just setup-demo` | Install dependencies + Playwright browser |
| `just site-dev` | Start Astro dev server with hot reload |
| `just site-build` | Production build to `site/dist/` |
| `just site-preview` | Build + preview production bundle |
| `just site-deploy` | Build + deploy to Cloudflare Workers |
| `just site-deploy-dry` | Validate deploy without publishing |
| `just site-cf-dev` | Run wrangler dev (Workers runtime locally) |
| `just demo-test` | Run Vitest unit tests |
| `just demo-test-cov` | Unit tests with coverage report |
| `just demo-test-e2e` | Run Playwright E2E tests (headless) |
| `just demo-test-e2e-headed` | E2E tests with visible browser |
| `just demo-test-all` | Unit tests + E2E tests |
| `just site-lint` | ESLint check |
| `just site-check` | Lint + unit + E2E (full CI check) |
