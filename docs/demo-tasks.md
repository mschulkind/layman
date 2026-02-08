# Layman Interactive Demo — Task List

## Phase 1: Project Scaffolding
- [x] Initialize Vite + React + TypeScript project in `site/demo/`
- [x] Configure Tailwind CSS v4 via `@tailwindcss/vite`
- [x] Configure Vitest with jsdom, coverage, and setup file
- [x] Configure ESLint + TypeScript ESLint
- [x] Set up tsconfig files (app + node)
- [x] Add `@testing-library/react` and `@testing-library/jest-dom`
- [x] Add Framer Motion and Zustand
- [x] Create `src/test/setup.ts` with jest-dom import
- [x] Verify `npm run dev`, `npm run test`, `npm run build` all work

## Phase 2: Core Layout Engine
- [x] Define shared types in `src/layouts/types.ts` (Rect, WindowInfo, WindowRect, LayoutConfig, LayoutFn)
- [x] Implement `masterStack()` layout function
- [x] Write tests for MasterStack (0–6 windows, different masterWidth values, stack side)
- [x] Implement `autotiling()` layout function
- [x] Write tests for Autotiling (0–8 windows, depthLimit variations)
- [x] Implement `grid()` layout function
- [x] Write tests for Grid (0–9 windows, verify even distribution)
- [x] Implement `threeColumn()` layout function
- [x] Write tests for ThreeColumn (0–6 windows, balance stacks, masterWidth)
- [x] Verify ≥80% coverage on all layout files

## Phase 3: Window Management Store
- [x] Create Zustand store with window state (windows, focusedId, layout, config)
- [x] Implement actions: spawnWindow, closeWindow, focusNext, focusPrev, focusDirection
- [x] Implement actions: moveWindow, swapMaster, switchLayout
- [x] Compute layout positions as derived state
- [x] Write comprehensive store tests
- [x] Verify ≥80% coverage on store

## Phase 4: UI Components
- [x] Build `Window` component (title bar, number badge, placeholder image, focus glow)
- [x] Build `DemoContainer` component (monitor-shaped viewport, renders windows at computed positions)
- [x] Build `StatusBar` component (layout name, window count, focused ID)
- [x] Build `HelpOverlay` component (keyboard shortcut reference)
- [x] Build `LayoutSwitcher` component (pill buttons for layout selection)
- [x] Write component tests with Testing Library
- [x] Verify ≥80% coverage on component files

## Phase 5: Keyboard System
- [x] Create `useKeyboard` hook mapping keys → store actions
- [x] Implement all keybindings from design doc
- [x] Prevent default browser behavior for bound keys when demo is focused
- [x] Write keyboard hook tests
- [x] Verify ≥80% coverage on keyboard hook

## Phase 6: Polish & Integration
- [x] Add Framer Motion layout animations for window transitions
- [x] Style everything to match landing page theme (colors, fonts, border radii)
- [x] Add window content (placekitten images + window number)
- [x] Configure Vite build output to `site/demo/dist/`
- [x] Test production build
- [x] Final coverage check across all files (≥80% each)
- [x] Run lint and fix any issues
