import { useEffect, useRef } from "react";
import { useWindowStore } from "../store/window-store";
import { Window } from "./Window";
import { LayoutToast } from "./LayoutToast";
import { AnimatePresence } from "framer-motion";

export function DemoContainer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const windows = useWindowStore((s) => s.windows);
  const setContainerRect = useWindowStore((s) => s.setContainerRect);
  const getLayoutRects = useWindowStore((s) => s.getLayoutRects);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setContainerRect({ x: 0, y: 0, width, height });
      }
    });

    observer.observe(el);
    const { width, height } = el.getBoundingClientRect();
    setContainerRect({ x: 0, y: 0, width, height });

    return () => observer.disconnect();
  }, [setContainerRect]);

  const rects = getLayoutRects();
  const containerRect = useWindowStore((s) => s.containerRect);

  return (
    <div
      ref={containerRef}
      data-testid="demo-container"
      className="relative min-h-0 flex-1 overflow-hidden rounded-lg border border-border bg-bg-secondary"
      tabIndex={0}
    >
      <div
        className="pointer-events-none absolute inset-0 z-50 opacity-[0.03]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)",
        }}
      />

      {windows.length === 0 && (
        <div
          className="flex h-full w-full flex-col items-center justify-center gap-3 text-text-muted"
          data-testid="empty-state"
        >
          <div className="text-5xl">🪟</div>
          <p className="text-sm">
            Press{" "}
            <kbd className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-xs text-accent-light">
              N
            </kbd>{" "}
            to spawn a window
          </p>
        </div>
      )}

      <AnimatePresence>
        {rects.map((wr) => {
          const win = windows.find((w) => w.id === wr.id);
          if (!win) return null;
          return (
            <Window
              key={win.id}
              window={win}
              rect={wr.rect}
              containerWidth={containerRect.width}
              containerHeight={containerRect.height}
            />
          );
        })}
      </AnimatePresence>

      <LayoutToast />
    </div>
  );
}
