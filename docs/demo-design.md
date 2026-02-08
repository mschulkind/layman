# Layman Interactive Demo — Design Document

## Overview

An interactive, keyboard-driven tiling window manager simulator embedded in the layman landing page. Users can spawn, close, focus, and rearrange windows using keyboard shortcuts — experiencing layman's layout algorithms (MasterStack, Autotiling, Grid, ThreeColumn) directly in the browser.

## Goals

1. **Demonstrate, don't describe** — let visitors *feel* how tiling layouts work.
2. **Keyboard-first** — all operations via keybindings, matching real layman config.
3. **Faithful layouts** — each layout algorithm should produce the same visual result as layman running on Sway.
4. **Visually polished** — dark theme consistent with the existing landing page, smooth animations, clear focus indicators.
5. **Well-tested** — ≥80% line coverage per source file, unit tests with Vitest + Testing Library.

## Tech Stack

Modeled after `~/code/songtv/frontend` and `~/code/vantage/frontend`:

| Tool | Purpose |
|------|---------|
| **Vite** | Build tool & dev server |
| **React 19** | UI rendering |
| **TypeScript** | Type safety |
| **Tailwind CSS v4** | Styling via `@tailwindcss/vite` plugin |
| **Zustand** | Lightweight state management for window/layout state |
| **Vitest + jsdom** | Unit testing |
| **@testing-library/react** | Component tests |
| **@vitest/coverage-v8** | Coverage reporting |
| **ESLint + Prettier** | Lint & format |
| **Framer Motion** | Layout transition animations |

## Architecture

```
site/demo/
├── index.html
├── package.json
├── vite.config.ts
├── vitest.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css           # Tailwind imports + theme tokens
│   ├── layouts/             # Pure layout computation functions
│   │   ├── types.ts         # Shared types (Rect, Window, LayoutResult)
│   │   ├── master-stack.ts
│   │   ├── autotiling.ts
│   │   ├── grid.ts
│   │   ├── three-column.ts
│   │   ├── master-stack.test.ts
│   │   ├── autotiling.test.ts
│   │   ├── grid.test.ts
│   │   └── three-column.test.ts
│   ├── store/
│   │   ├── window-store.ts  # Zustand store
│   │   └── window-store.test.ts
│   ├── hooks/
│   │   ├── use-keyboard.ts  # Keyboard shortcut handler
│   │   └── use-keyboard.test.ts
│   ├── components/
│   │   ├── DemoContainer.tsx
│   │   ├── DemoContainer.test.tsx
│   │   ├── Window.tsx
│   │   ├── Window.test.tsx
│   │   ├── StatusBar.tsx
│   │   ├── StatusBar.test.tsx
│   │   ├── HelpOverlay.tsx
│   │   ├── HelpOverlay.test.tsx
│   │   ├── LayoutSwitcher.tsx
│   │   └── LayoutSwitcher.test.tsx
│   └── test/
│       └── setup.ts
```

## Layout Engine

Each layout is a **pure function**:

```typescript
type LayoutFn = (windows: WindowInfo[], containerRect: Rect, config: LayoutConfig) => WindowRect[];
```

### MasterStack
- Master window occupies `masterWidth%` of container width (default 50%).
- Stack windows split the remaining space vertically.
- New windows become master; old master pushes to top of stack.

### Autotiling
- Binary-split algorithm: if `height > width`, split vertically; else horizontally.
- Creates a spiral-like recursive pattern.
- `depthLimit` config option caps nesting.

### Grid
- Distributes windows evenly into rows and columns.
- Algorithm: `cols = ceil(sqrt(n))`, `rows = ceil(n / cols)`.
- Last row may have fewer windows, centered or left-aligned.

### ThreeColumn
- Center master column at `masterWidth%`.
- Left and right stacks split remaining space equally.
- Windows distributed to stacks alternating or right-first.

## Window Content

Each spawned window displays:
- A **window number** (1, 2, 3…)
- A **placeholder kitten image** from `https://placekitten.com/{width}/{height}` or a color-coded gradient
- A **title bar** with the window number and a simulated app name (Terminal, Browser, Editor, etc.)

## Keyboard Shortcuts

Matching layman's real keybindings:

| Key | Action |
|-----|--------|
| `N` | New window (spawn) |
| `Q` | Close focused window |
| `H` / `←` | Focus left / previous |
| `L` / `→` | Focus right / next |
| `J` / `↓` | Focus down / stack down |
| `K` / `↑` | Focus up / stack up |
| `Shift+H` | Move window left |
| `Shift+L` | Move window right |
| `Shift+J` | Move window down |
| `Shift+K` | Move window up |
| `Enter` | Swap with master |
| `1` | Switch to MasterStack |
| `2` | Switch to Autotiling |
| `3` | Switch to Grid |
| `4` | Switch to ThreeColumn |
| `?` | Toggle help overlay |

## UI Design

- **Container**: 16:10 aspect ratio box styled like a monitor, with a thin border and rounded corners. Dark background matching `--bg-card` from the landing page.
- **Windows**: Rounded rectangles with a colored title bar, window number badge, and placeholder content. Focused window has an accent-colored border glow (`--accent` / `#6366f1`).
- **Status bar**: Bottom bar showing current layout name, window count, and focused window ID.
- **Help overlay**: Semi-transparent modal listing all keyboard shortcuts, toggled with `?`.
- **Layout switcher**: Row of pill buttons above the container (matching existing `.layout-tab` style).
- **Transitions**: Framer Motion `layoutId` for smooth window resize/reposition animations.

## Integration with Landing Page

The demo will be built as a standalone Vite app in `site/demo/`. The build output goes to `site/demo/dist/` and can be:

1. **Embedded via iframe** in the existing `site/index.html`, or
2. **Linked** as a standalone page at `/demo/`.

The production build is a static bundle (HTML + JS + CSS) with no backend dependencies.

## Testing Strategy

- **Layout functions**: Pure input→output tests. Given N windows and a container rect, assert exact positions and sizes. Edge cases: 0 windows, 1 window, many windows.
- **Store**: Test all actions (spawn, close, focus, move, switch layout) produce correct state.
- **Keyboard hook**: Test that keydown events dispatch correct store actions.
- **Components**: Render tests with Testing Library — verify windows appear, focus highlights, layout switches.
- **Coverage target**: ≥80% per file, enforced in CI.
