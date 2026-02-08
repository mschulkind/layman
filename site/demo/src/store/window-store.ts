import { create } from "zustand";
import type { LayoutConfig, LayoutName, Rect, WindowRect } from "../layouts/types";
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

export interface WindowStore {
  windows: WindowData[];
  focusedId: string | null;
  layout: LayoutName;
  config: LayoutConfig;
  showHelp: boolean;
  nextNumber: number;
  containerRect: Rect;

  spawnWindow: () => void;
  closeWindow: () => void;
  closeFocusedWindow: () => void;
  focusNext: () => void;
  focusPrev: () => void;
  focusWindow: (id: string) => void;
  swapMaster: () => void;
  moveWindowUp: () => void;
  moveWindowDown: () => void;
  switchLayout: (layout: LayoutName) => void;
  toggleHelp: () => void;
  setContainerRect: (rect: Rect) => void;
  getLayoutRects: () => WindowRect[];
}

const layoutFns = {
  MasterStack: masterStack,
  Autotiling: autotiling,
  Grid: grid,
  ThreeColumn: threeColumn,
};

export const useWindowStore = create<WindowStore>((set, get) => ({
  windows: [],
  focusedId: null,
  layout: "MasterStack",
  config: { masterWidth: 50, stackSide: "right", balanceStacks: true },
  showHelp: false,
  nextNumber: 1,
  containerRect: { x: 0, y: 0, width: 1000, height: 600 },

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

  switchLayout: (layout: LayoutName) => set({ layout }),

  toggleHelp: () => set((state) => ({ showHelp: !state.showHelp })),

  setContainerRect: (rect: Rect) => set({ containerRect: rect }),

  getLayoutRects: () => {
    const state = get();
    const fn = layoutFns[state.layout];
    const ids = state.windows.map((w) => w.id);
    return fn(ids, state.containerRect, state.config);
  },
}));
