# Interactive Demo

The Layman interactive demo is a browser-based simulator that lets users
experience tiling window management without installing anything. It renders
animated windows inside a virtual monitor and responds to keyboard shortcuts
mirroring real Layman keybindings.

**Live demo:** <https://layman.pages.dev/demo/>

## Running Locally

### First-time setup

```bash
just setup-demo
```

This installs npm dependencies and the Playwright Chromium browser.

### Dev server (hot reload)

```bash
just demo-dev
```

Opens on `http://localhost:5173/demo/`. Changes to source files are reflected
instantly.

### Production preview

```bash
just demo-preview
```

Builds the demo and serves it from `http://localhost:4173/demo/` — exactly how
it will look when deployed.

## Deployment

The demo is deployed automatically as part of Cloudflare Pages.

### How it works

1. `wrangler.toml` sets `pages_build_output_dir = "site"`, so the entire
   `site/` directory is deployed.
2. The Vite config sets `base: "/demo/"` and builds into `site/demo/dist/`.
3. The `wrangler.toml` build command runs `npm install && npm run build`,
   then replaces the source files with the build output so that
   `site/demo/index.html` serves the production bundle at `/demo/`.

### Build for deployment

```bash
just demo-build
```

Output lands in `site/demo/dist/`.

## Project Structure

```text
site/demo/
├── e2e/                    # Playwright E2E tests
│   └── demo.spec.ts
├── src/
│   ├── components/         # React UI components
│   │   ├── DemoContainer.tsx   # Virtual monitor viewport
│   │   ├── HelpOverlay.tsx     # Keyboard shortcut reference
│   │   ├── LayoutSwitcher.tsx  # Layout selection buttons
│   │   ├── StatusBar.tsx       # Layout name + window count
│   │   └── Window.tsx          # Individual tiled window
│   ├── hooks/
│   │   └── use-keyboard.ts    # Keyboard shortcut handler
│   ├── layouts/            # Pure layout engine (no React)
│   │   ├── autotiling.ts
│   │   ├── grid.ts
│   │   ├── master-stack.ts
│   │   ├── three-column.ts
│   │   ├── types.ts
│   │   └── index.ts
│   ├── store/
│   │   └── window-store.ts    # Zustand state management
│   ├── test/
│   │   └── setup.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── playwright.config.ts
├── vitest.config.ts
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### Architecture layers

| Layer | Purpose |
|-------|---------|
| **Layouts** (`src/layouts/`) | Pure functions that compute window positions from a list of windows + container rect. Zero React dependencies. |
| **Store** (`src/store/`) | Zustand store managing windows, focus, layout selection, and all user actions. |
| **Hooks** (`src/hooks/`) | `useKeyboard` maps keyboard events to store actions. |
| **Components** (`src/components/`) | React components rendering the virtual desktop. Framer Motion handles layout animations. |

## Tech Stack

- **Vite** — build tool and dev server
- **React 19** — UI framework
- **TypeScript** — type safety
- **Tailwind CSS v4** — styling (via `@tailwindcss/vite`)
- **Zustand** — state management
- **Framer Motion** — layout animations
- **Vitest** — unit tests (jsdom)
- **Playwright** — E2E browser tests

## Testing

### Unit tests (Vitest)

```bash
just demo-test        # Run once
just demo-test-cov    # Run with coverage report
```

Unit tests cover the layout engine, Zustand store, React components, and
keyboard hook. 98 tests, 96%+ statement coverage.

### E2E browser tests (Playwright)

```bash
just demo-test-e2e          # Headless (CI-friendly)
just demo-test-e2e-headed   # Visible browser (debugging)
```

Playwright tests build the production bundle, start a preview server, and
drive a real Chromium browser. They verify:

- Page loads with correct initial state
- Keyboard shortcuts spawn/close/focus windows
- Layout switcher buttons work
- Help overlay opens and closes
- Focus navigation cycles through windows
- Full spawn → switch → navigate → close workflow

18 E2E tests covering all user-facing functionality.

### Run everything

```bash
just demo-check   # Lint + unit tests + E2E tests
```

This is also included in the top-level `just check`.

## Keyboard Shortcuts

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
| `just demo-dev` | Start Vite dev server with hot reload |
| `just demo-build` | Production build to `site/demo/dist/` |
| `just demo-preview` | Build + preview production bundle |
| `just demo-test` | Run Vitest unit tests |
| `just demo-test-cov` | Unit tests with coverage report |
| `just demo-test-e2e` | Run Playwright E2E tests (headless) |
| `just demo-test-e2e-headed` | E2E tests with visible browser |
| `just demo-test-all` | Unit tests + E2E tests |
| `just demo-lint` | ESLint check |
| `just demo-check` | Lint + unit + E2E (full CI check) |
