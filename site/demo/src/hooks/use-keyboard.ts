import { useEffect } from "react";
import { useWindowStore } from "../store/window-store";
import type { LayoutName } from "../layouts/types";

const LAYOUT_KEYS: Record<string, LayoutName> = {
  "1": "MasterStack",
  "2": "Autotiling",
  "3": "Grid",
  "4": "ThreeColumn",
};

export function useKeyboard() {
  const store = useWindowStore;

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      const key = e.key;
      const shift = e.shiftKey;

      // Layout switching: 1-4
      if (!shift && key in LAYOUT_KEYS) {
        e.preventDefault();
        store.getState().switchLayout(LAYOUT_KEYS[key]);
        return;
      }

      if (key === "n" && !shift) {
        e.preventDefault();
        store.getState().spawnWindow();
        return;
      }

      if (key === "q" && !shift) {
        e.preventDefault();
        store.getState().closeFocusedWindow();
        return;
      }

      if ((key === "l" || key === "ArrowRight") && !shift) {
        e.preventDefault();
        store.getState().focusNext();
        return;
      }
      if ((key === "h" || key === "ArrowLeft") && !shift) {
        e.preventDefault();
        store.getState().focusPrev();
        return;
      }
      if ((key === "j" || key === "ArrowDown") && !shift) {
        e.preventDefault();
        store.getState().focusNext();
        return;
      }
      if ((key === "k" || key === "ArrowUp") && !shift) {
        e.preventDefault();
        store.getState().focusPrev();
        return;
      }

      if (key === "K" && shift) {
        e.preventDefault();
        store.getState().moveWindowUp();
        return;
      }
      if (key === "J" && shift) {
        e.preventDefault();
        store.getState().moveWindowDown();
        return;
      }

      if (key === "Enter") {
        e.preventDefault();
        store.getState().swapMaster();
        return;
      }

      if (key === "?") {
        e.preventDefault();
        store.getState().toggleHelp();
        return;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [store]);
}
