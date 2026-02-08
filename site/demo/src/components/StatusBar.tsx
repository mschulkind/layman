import { useWindowStore } from "../store/window-store";

export function StatusBar() {
  const layout = useWindowStore((s) => s.layout);
  const windowCount = useWindowStore((s) => s.windows.length);
  const focusedId = useWindowStore((s) => s.focusedId);
  const windows = useWindowStore((s) => s.windows);
  const focusedWindow = windows.find((w) => w.id === focusedId);

  return (
    <div
      data-testid="status-bar"
      className="flex w-full max-w-4xl items-center justify-between rounded-lg border border-border bg-bg-card px-4 py-2 font-mono text-xs"
    >
      <div className="flex items-center gap-4">
        <span className="text-accent-light">{layout}</span>
        <span className="text-text-muted">|</span>
        <span className="text-text-secondary">
          {windowCount} {windowCount === 1 ? "window" : "windows"}
        </span>
      </div>
      <div className="flex items-center gap-4">
        {focusedWindow && (
          <span className="text-text-secondary">
            focused:{" "}
            <span className="text-text-primary">
              {focusedWindow.appName} #{focusedWindow.number}
            </span>
          </span>
        )}
      </div>
    </div>
  );
}
