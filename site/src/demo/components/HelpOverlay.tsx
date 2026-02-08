import { useWindowStore } from "../store/window-store";

const SHORTCUTS = [
  { key: "N", action: "Spawn window" },
  { key: "Q", action: "Close focused window" },
  { key: "H / ←", action: "Focus previous" },
  { key: "L / →", action: "Focus next" },
  { key: "Shift+K", action: "Move window up" },
  { key: "Shift+J", action: "Move window down" },
  { key: "Enter", action: "Swap with master" },
  { key: "1–4", action: "Switch layout" },
  { key: "?", action: "Toggle this help" },
];

export function HelpOverlay() {
  const showHelp = useWindowStore((s) => s.showHelp);
  const toggleHelp = useWindowStore((s) => s.toggleHelp);

  if (!showHelp) return null;

  return (
    <div
      data-testid="help-overlay"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={toggleHelp}
    >
      <div
        className="w-full max-w-md rounded-xl border border-border bg-bg-card p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-bold text-text-primary">
          ⌨️ Keyboard Shortcuts
        </h2>
        <div className="space-y-2">
          {SHORTCUTS.map(({ key, action }) => (
            <div
              key={key}
              className="flex items-center justify-between rounded-lg px-3 py-2 odd:bg-bg-tertiary"
            >
              <kbd className="rounded bg-bg-secondary px-2 py-0.5 font-mono text-sm text-accent-light">
                {key}
              </kbd>
              <span className="text-sm text-text-secondary">{action}</span>
            </div>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-text-muted">
          Click outside or press{" "}
          <kbd className="font-mono text-accent-light">?</kbd> to close
        </p>
      </div>
    </div>
  );
}
