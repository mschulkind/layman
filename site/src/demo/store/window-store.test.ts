import { describe, it, expect, beforeEach } from "vitest";
import { useWindowStore } from "./window-store";

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

describe("window-store", () => {
  beforeEach(resetStore);

  describe("spawnWindow", () => {
    it("adds a window and focuses it", () => {
      useWindowStore.getState().spawnWindow();
      const state = useWindowStore.getState();
      expect(state.windows).toHaveLength(1);
      expect(state.windows[0].id).toBe("win-1");
      expect(state.focusedId).toBe("win-1");
    });

    it("new window becomes master (index 0)", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      const state = useWindowStore.getState();
      expect(state.windows[0].id).toBe("win-2");
      expect(state.windows[1].id).toBe("win-1");
    });

    it("increments the counter", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      expect(useWindowStore.getState().nextNumber).toBe(3);
    });

    it("assigns app names cyclically", () => {
      for (let i = 0; i < 11; i++) {
        useWindowStore.getState().spawnWindow();
      }
      const names = useWindowStore
        .getState()
        .windows.map((w) => w.appName);
      expect(names).toContain("Terminal");
    });
  });

  describe("closeWindow / closeFocusedWindow", () => {
    it("removes the focused window", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().closeFocusedWindow();
      expect(useWindowStore.getState().windows).toHaveLength(1);
    });

    it("moves focus to next window after close", () => {
      useWindowStore.getState().spawnWindow(); // win-1
      useWindowStore.getState().spawnWindow(); // win-2 (focused)
      useWindowStore.getState().closeFocusedWindow();
      expect(useWindowStore.getState().focusedId).toBe("win-1");
    });

    it("sets focusedId to null when last window closed", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().closeFocusedWindow();
      expect(useWindowStore.getState().focusedId).toBeNull();
    });

    it("no-ops on empty window list", () => {
      useWindowStore.getState().closeWindow();
      expect(useWindowStore.getState().windows).toHaveLength(0);
    });
  });

  describe("focusNext / focusPrev", () => {
    it("focusNext wraps around", () => {
      useWindowStore.getState().spawnWindow(); // win-1
      useWindowStore.getState().spawnWindow(); // win-2 (focused)
      // windows: [win-2, win-1], focused: win-2 (idx 0)
      useWindowStore.getState().focusNext(); // → win-1
      expect(useWindowStore.getState().focusedId).toBe("win-1");
      useWindowStore.getState().focusNext(); // wraps → win-2
      expect(useWindowStore.getState().focusedId).toBe("win-2");
    });

    it("focusPrev wraps around", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      // focused: win-2 (idx 0)
      useWindowStore.getState().focusPrev(); // wraps → win-1
      expect(useWindowStore.getState().focusedId).toBe("win-1");
    });

    it("no-ops on empty list", () => {
      useWindowStore.getState().focusNext();
      expect(useWindowStore.getState().focusedId).toBeNull();
    });
  });

  describe("focusWindow", () => {
    it("sets focusedId directly", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().focusWindow("win-1");
      expect(useWindowStore.getState().focusedId).toBe("win-1");
    });
  });

  describe("swapMaster", () => {
    it("swaps focused window with master", () => {
      useWindowStore.getState().spawnWindow(); // win-1
      useWindowStore.getState().spawnWindow(); // win-2 (master)
      useWindowStore.getState().focusWindow("win-1");
      useWindowStore.getState().swapMaster();
      const ids = useWindowStore.getState().windows.map((w) => w.id);
      expect(ids[0]).toBe("win-1");
      expect(ids[1]).toBe("win-2");
    });

    it("no-ops when focused is already master", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      // win-2 is focused and master
      useWindowStore.getState().swapMaster();
      expect(useWindowStore.getState().windows[0].id).toBe("win-2");
    });

    it("no-ops with fewer than 2 windows", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().swapMaster();
      expect(useWindowStore.getState().windows[0].id).toBe("win-1");
    });
  });

  describe("moveWindowUp / moveWindowDown", () => {
    it("moveWindowUp swaps with previous", () => {
      useWindowStore.getState().spawnWindow(); // win-1
      useWindowStore.getState().spawnWindow(); // win-2
      useWindowStore.getState().spawnWindow(); // win-3
      // windows: [win-3, win-2, win-1], focused: win-3 (idx 0)
      useWindowStore.getState().focusWindow("win-1");
      useWindowStore.getState().moveWindowUp();
      const ids = useWindowStore.getState().windows.map((w) => w.id);
      expect(ids).toEqual(["win-3", "win-1", "win-2"]);
    });

    it("moveWindowDown swaps with next", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().focusWindow("win-3");
      useWindowStore.getState().moveWindowDown();
      const ids = useWindowStore.getState().windows.map((w) => w.id);
      expect(ids).toEqual(["win-2", "win-3", "win-1"]);
    });

    it("moveWindowUp no-ops at position 0", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().moveWindowUp(); // focused is at idx 0
      expect(useWindowStore.getState().windows[0].id).toBe("win-2");
    });

    it("moveWindowDown no-ops at last position", () => {
      useWindowStore.getState().spawnWindow(); // win-1 at last
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().focusWindow("win-1");
      useWindowStore.getState().moveWindowDown();
      expect(
        useWindowStore.getState().windows.map((w) => w.id),
      ).toEqual(["win-2", "win-1"]);
    });
  });

  describe("switchLayout", () => {
    it("changes layout", () => {
      useWindowStore.getState().switchLayout("Grid");
      expect(useWindowStore.getState().layout).toBe("Grid");
    });
  });

  describe("toggleHelp", () => {
    it("toggles showHelp", () => {
      expect(useWindowStore.getState().showHelp).toBe(false);
      useWindowStore.getState().toggleHelp();
      expect(useWindowStore.getState().showHelp).toBe(true);
      useWindowStore.getState().toggleHelp();
      expect(useWindowStore.getState().showHelp).toBe(false);
    });
  });

  describe("setContainerRect", () => {
    it("updates containerRect", () => {
      const rect = { x: 10, y: 20, width: 800, height: 500 };
      useWindowStore.getState().setContainerRect(rect);
      expect(useWindowStore.getState().containerRect).toEqual(rect);
    });
  });

  describe("getLayoutRects", () => {
    it("returns rects for current windows and layout", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      const rects = useWindowStore.getState().getLayoutRects();
      expect(rects).toHaveLength(2);
      expect(rects[0].id).toBe("win-2");
    });

    it("returns empty for no windows", () => {
      expect(useWindowStore.getState().getLayoutRects()).toEqual([]);
    });
  });

  describe("switchLayout", () => {
    it("sets layout toast", () => {
      useWindowStore.getState().switchLayout("Grid");
      expect(useWindowStore.getState().layoutToast).toContain("grid");
    });

    it("dismissToast clears the toast", () => {
      useWindowStore.getState().switchLayout("Grid");
      useWindowStore.getState().dismissToast();
      expect(useWindowStore.getState().layoutToast).toBeNull();
    });
  });

  describe("focusDirection", () => {
    it("MasterStack: up/down cycle linearly", () => {
      useWindowStore.getState().spawnWindow(); // win-1
      useWindowStore.getState().spawnWindow(); // win-2 (focused, idx 0)
      // down → focusNext → win-1
      useWindowStore.getState().focusDirection("down");
      expect(useWindowStore.getState().focusedId).toBe("win-1");
      // up → focusPrev → win-2
      useWindowStore.getState().focusDirection("up");
      expect(useWindowStore.getState().focusedId).toBe("win-2");
    });

    it("MasterStack: left/right are no-ops", () => {
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      const before = useWindowStore.getState().focusedId;
      useWindowStore.getState().focusDirection("left");
      expect(useWindowStore.getState().focusedId).toBe(before);
      useWindowStore.getState().focusDirection("right");
      expect(useWindowStore.getState().focusedId).toBe(before);
    });

    it("Grid: all directions cycle linearly", () => {
      useWindowStore.getState().switchLayout("Grid");
      useWindowStore.getState().spawnWindow();
      useWindowStore.getState().spawnWindow();
      // right → focusNext
      useWindowStore.getState().focusDirection("right");
      expect(useWindowStore.getState().focusedId).toBe("win-1");
      // left → focusPrev
      useWindowStore.getState().focusDirection("left");
      expect(useWindowStore.getState().focusedId).toBe("win-2");
    });

    it("no-ops on empty window list", () => {
      useWindowStore.getState().focusDirection("down");
      expect(useWindowStore.getState().focusedId).toBeNull();
    });
  });
});
