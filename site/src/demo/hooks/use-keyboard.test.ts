import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useKeyboard } from "./use-keyboard";
import { useWindowStore } from "../store/window-store";

function resetStore() {
  useWindowStore.setState({
    windows: [],
    focusedId: null,
    layout: "MasterStack",
    config: { masterWidth: 50, stackSide: "right", balanceStacks: true },
    showHelp: false,
    nextNumber: 1,
    containerRect: { x: 0, y: 0, width: 1000, height: 600 },
    layoutToast: null,
  });
}

function pressKey(key: string, opts: Partial<KeyboardEventInit> = {}) {
  window.dispatchEvent(
    new KeyboardEvent("keydown", { key, bubbles: true, ...opts }),
  );
}

describe("useKeyboard", () => {
  beforeEach(resetStore);

  it("N spawns a window", () => {
    renderHook(() => useKeyboard());
    pressKey("n");
    expect(useWindowStore.getState().windows).toHaveLength(1);
  });

  it("Q closes focused window", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    pressKey("q");
    expect(useWindowStore.getState().windows).toHaveLength(0);
  });

  it("J/ArrowDown focuses next in MasterStack", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    // focused: win-2 (idx 0), win-1 (idx 1)
    pressKey("j");
    expect(useWindowStore.getState().focusedId).toBe("win-1");
  });

  it("K/ArrowUp focuses prev in MasterStack", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    // focused: win-2 (idx 0)
    pressKey("k");
    // wraps to last: win-1
    expect(useWindowStore.getState().focusedId).toBe("win-1");
  });

  it("L/ArrowRight are no-ops in MasterStack", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    // focused: win-2 (idx 0)
    pressKey("l");
    expect(useWindowStore.getState().focusedId).toBe("win-2");
    pressKey("ArrowRight");
    expect(useWindowStore.getState().focusedId).toBe("win-2");
  });

  it("H/ArrowLeft are no-ops in MasterStack", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    pressKey("h");
    expect(useWindowStore.getState().focusedId).toBe("win-2");
  });

  it("L/H navigate in Grid layout", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().switchLayout("Grid");
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    // focused: win-2 (idx 0)
    pressKey("l");
    expect(useWindowStore.getState().focusedId).toBe("win-1");
    pressKey("h");
    expect(useWindowStore.getState().focusedId).toBe("win-2");
  });

  it("1-4 switch layouts", () => {
    renderHook(() => useKeyboard());
    pressKey("2");
    expect(useWindowStore.getState().layout).toBe("Autotiling");
    pressKey("3");
    expect(useWindowStore.getState().layout).toBe("Grid");
    pressKey("4");
    expect(useWindowStore.getState().layout).toBe("ThreeColumn");
    pressKey("1");
    expect(useWindowStore.getState().layout).toBe("MasterStack");
  });

  it("Shift+K moves window up", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().focusWindow("win-1");
    pressKey("K", { shiftKey: true });
    const ids = useWindowStore.getState().windows.map((w) => w.id);
    expect(ids).toEqual(["win-3", "win-1", "win-2"]);
  });

  it("Shift+J moves window down", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    pressKey("J", { shiftKey: true });
    const ids = useWindowStore.getState().windows.map((w) => w.id);
    expect(ids).toEqual(["win-2", "win-3", "win-1"]);
  });

  it("Enter swaps with master", () => {
    renderHook(() => useKeyboard());
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().spawnWindow();
    useWindowStore.getState().focusWindow("win-1");
    pressKey("Enter");
    expect(useWindowStore.getState().windows[0].id).toBe("win-1");
  });

  it("? toggles help", () => {
    renderHook(() => useKeyboard());
    pressKey("?");
    expect(useWindowStore.getState().showHelp).toBe(true);
    pressKey("?");
    expect(useWindowStore.getState().showHelp).toBe(false);
  });

  it("ignores keys when focused on input", () => {
    renderHook(() => useKeyboard());
    const input = document.createElement("input");
    document.body.appendChild(input);
    const event = new KeyboardEvent("keydown", {
      key: "n",
      bubbles: true,
    });
    Object.defineProperty(event, "target", { value: input });
    window.dispatchEvent(event);
    expect(useWindowStore.getState().windows).toHaveLength(0);
    document.body.removeChild(input);
  });

  it("cleans up event listener on unmount", () => {
    const spy = vi.spyOn(window, "removeEventListener");
    const { unmount } = renderHook(() => useKeyboard());
    unmount();
    expect(spy).toHaveBeenCalledWith("keydown", expect.any(Function));
    spy.mockRestore();
  });
});
