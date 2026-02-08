import { create } from "zustand";
import type {
  LayoutConfig,
  LayoutName,
  Rect,
  WindowRect,
} from "../layouts/types";
import { masterStack } from "../layouts/master-stack";
import { autotiling } from "../layouts/autotiling";
import { grid } from "../layouts/grid";
import { threeColumn } from "../layouts/three-column";

const APP_NAMES = [
  "Terminal",
  "Browser",
  "Editor",
  "Files",
  "Music",
  "Settings",
  "Monitor",
  "Chat",
  "Notes",
  "Mail",
];

export interface WindowData {
  id: string;
  number: number;
  appName: string;
  imageIndex: number;
}

export type FocusDirection = "up" | "down" | "left" | "right";

export interface WindowStore {
  windows: WindowData[];
  focusedId: string | null;
  layout: LayoutName;
  config: LayoutConfig;
  showHelp: boolean;
  nextNumber: number;
  containerRect: Rect;
  layoutToast: string | null;

  spawnWindow: () => void;
  closeWindow: () => void;
  closeFocusedWindow: () => void;
  focusNext: () => void;
  focusPrev: () => void;
  focusWindow: (id: string) => void;
  focusDirection: (dir: FocusDirection) => void;
  swapMaster: () => void;
  moveWindowUp: () => void;
  moveWindowDown: () => void;
  switchLayout: (layout: LayoutName) => void;
  toggleHelp: () => void;
  setContainerRect: (rect: Rect) => void;
  getLayoutRects: () => WindowRect[];
  dismissToast: () => void;
}

const layoutFns = {
  MasterStack: masterStack,
  Autotiling: autotiling,
  Grid: grid,
  ThreeColumn: threeColumn,
};

export const LAYOUT_DESCRIPTIONS: Record<LayoutName, string> = {
  MasterStack:
    "One master window + vertical stack. ↑↓ cycles all windows linearly.",
  Autotiling:
    "Alternating horizontal/vertical splits in a spiral pattern.",
  Grid: "Even grid layout. Columns = ⌈√n⌉.",
  ThreeColumn:
    "Center master + left/right stacks. ←→ between columns, ↑↓ within.",
};

/**
 * ThreeColumn: determine which column a window is in.
 */
function getColumnForWindow(
  windowId: string,
  rects: WindowRect[],
  container: Rect,
  config: LayoutConfig,
): "left" | "master" | "right" | null {
  if (rects.length === 0) return null;
  const wr = rects.find((r) => r.id === windowId);
  if (!wr) return null;
  if (rects[0].id === windowId) return "master";

  const masterFrac = config.masterWidth / 100;
  const masterW = Math.round(container.width * masterFrac);
  const sideW = Math.round((container.width - masterW) / 2);
  const masterX = container.x + sideW;

  if (wr.rect.x < masterX) return "left";
  if (wr.rect.x >= masterX + masterW) return "right";
  return "master";
}

function getWindowsInColumn(
  column: "left" | "master" | "right",
  windowIds: string[],
  rects: WindowRect[],
  container: Rect,
  config: LayoutConfig,
): string[] {
  return windowIds.filter(
    (id) => getColumnForWindow(id, rects, container, config) === column,
  );
}

export const useWindowStore = create<WindowStore>((set, get) => ({
  windows: [],
  focusedId: null,
  layout: "MasterStack",
  config: { masterWidth: 50, stackSide: "right", balanceStacks: true },
  showHelp: false,
  nextNumber: 1,
  containerRect: { x: 0, y: 0, width: 1000, height: 600 },
  layoutToast: null,

  spawnWindow: () =>
    set((state) => {
      const num = state.nextNumber;
      const newWindow: WindowData = {
        id: `win-${num}`,
        number: num,
        appName: APP_NAMES[(num - 1) % APP_NAMES.length],
        imageIndex: num,
      };
      return {
        windows: [newWindow, ...state.windows],
        focusedId: newWindow.id,
        nextNumber: num + 1,
      };
    }),

  closeWindow: () =>
    set((state) => {
      if (state.windows.length === 0) return state;
      const idx = state.windows.findIndex((w) => w.id === state.focusedId);
      if (idx === -1) return state;
      const windows = state.windows.filter((w) => w.id !== state.focusedId);
      const newFocused =
        windows.length === 0
          ? null
          : windows[Math.min(idx, windows.length - 1)].id;
      return { windows, focusedId: newFocused };
    }),

  closeFocusedWindow: () => get().closeWindow(),

  focusNext: () =>
    set((state) => {
      if (state.windows.length === 0) return state;
      const idx = state.windows.findIndex((w) => w.id === state.focusedId);
      const next = (idx + 1) % state.windows.length;
      return { focusedId: state.windows[next].id };
    }),

  focusPrev: () =>
    set((state) => {
      if (state.windows.length === 0) return state;
      const idx = state.windows.findIndex((w) => w.id === state.focusedId);
      const prev = idx <= 0 ? state.windows.length - 1 : idx - 1;
      return { focusedId: state.windows[prev].id };
    }),

  focusWindow: (id: string) => set({ focusedId: id }),

  focusDirection: (dir: FocusDirection) => {
    const state = get();
    if (state.windows.length === 0) return;

    const layout = state.layout;

    if (layout === "MasterStack") {
      // 1D linear: up/down cycle through window list
      if (dir === "up") get().focusPrev();
      else if (dir === "down") get().focusNext();
      // left/right: no-op (matches real layman)
      return;
    }

    if (layout === "ThreeColumn") {
      // 2D: left/right between columns, up/down within column
      const rects = get().getLayoutRects();
      const { focusedId } = state;
      if (!focusedId || rects.length === 0) return;

      const currentCol = getColumnForWindow(
        focusedId,
        rects,
        state.containerRect,
        state.config,
      );
      if (!currentCol) return;

      if (dir === "left" || dir === "right") {
        const cols: ("left" | "master" | "right")[] = [
          "left",
          "master",
          "right",
        ];
        const colIdx = cols.indexOf(currentCol);
        const targetIdx =
          dir === "left"
            ? colIdx <= 0
              ? cols.length - 1
              : colIdx - 1
            : (colIdx + 1) % cols.length;
        const windowIds = state.windows.map((w) => w.id);
        const targets = getWindowsInColumn(
          cols[targetIdx],
          windowIds,
          rects,
          state.containerRect,
          state.config,
        );
        if (targets.length > 0) set({ focusedId: targets[0] });
      } else {
        // up/down within column
        if (currentCol === "master") return;
        const windowIds = state.windows.map((w) => w.id);
        const colWindows = getWindowsInColumn(
          currentCol,
          windowIds,
          rects,
          state.containerRect,
          state.config,
        );
        if (colWindows.length <= 1) return;
        const i = colWindows.indexOf(focusedId);
        const target =
          dir === "up"
            ? i <= 0
              ? colWindows.length - 1
              : i - 1
            : (i + 1) % colWindows.length;
        set({ focusedId: colWindows[target] });
      }
      return;
    }

    // Autotiling / Grid: linear cycle
    if (dir === "up" || dir === "left") get().focusPrev();
    else get().focusNext();
  },

  swapMaster: () =>
    set((state) => {
      if (state.windows.length < 2 || !state.focusedId) return state;
      const idx = state.windows.findIndex((w) => w.id === state.focusedId);
      if (idx <= 0) return state;
      const windows = [...state.windows];
      [windows[0], windows[idx]] = [windows[idx], windows[0]];
      return { windows };
    }),

  moveWindowUp: () =>
    set((state) => {
      if (state.windows.length < 2 || !state.focusedId) return state;
      const idx = state.windows.findIndex((w) => w.id === state.focusedId);
      if (idx <= 0) return state;
      const windows = [...state.windows];
      [windows[idx - 1], windows[idx]] = [windows[idx], windows[idx - 1]];
      return { windows };
    }),

  moveWindowDown: () =>
    set((state) => {
      if (state.windows.length < 2 || !state.focusedId) return state;
      const idx = state.windows.findIndex((w) => w.id === state.focusedId);
      if (idx === -1 || idx >= state.windows.length - 1) return state;
      const windows = [...state.windows];
      [windows[idx], windows[idx + 1]] = [windows[idx + 1], windows[idx]];
      return { windows };
    }),

  switchLayout: (layout: LayoutName) =>
    set({ layout, layoutToast: LAYOUT_DESCRIPTIONS[layout] }),

  toggleHelp: () => set((state) => ({ showHelp: !state.showHelp })),

  setContainerRect: (rect: Rect) => set({ containerRect: rect }),

  getLayoutRects: () => {
    const state = get();
    const fn = layoutFns[state.layout];
    const ids = state.windows.map((w) => w.id);
    return fn(ids, state.containerRect, state.config);
  },

  dismissToast: () => set({ layoutToast: null }),
}));
