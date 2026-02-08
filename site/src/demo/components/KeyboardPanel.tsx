import { useWindowStore } from "../store/window-store";
import type { LayoutName } from "../layouts/types";

interface Shortcut {
  key: string;
  action: string;
}

const COMMON_SHORTCUTS: Shortcut[] = [
  { key: "N", action: "Spawn window" },
  { key: "Q", action: "Close focused" },
  { key: "Enter", action: "Swap with master" },
  { key: "Shift+K", action: "Move up in list" },
  { key: "Shift+J", action: "Move down in list" },
  { key: "1–4", action: "Switch layout" },
];

const FOCUS_SHORTCUTS: Record<LayoutName, Shortcut[]> = {
  MasterStack: [
    { key: "↑ / K", action: "Focus prev (linear)" },
    { key: "↓ / J", action: "Focus next (linear)" },
    { key: "← →", action: "— (no-op)" },
  ],
  Autotiling: [
    { key: "↑ / K", action: "Focus prev" },
    { key: "↓ / J", action: "Focus next" },
    { key: "← / H", action: "Focus prev" },
    { key: "→ / L", action: "Focus next" },
  ],
  Grid: [
    { key: "↑ / K", action: "Focus prev" },
    { key: "↓ / J", action: "Focus next" },
    { key: "← / H", action: "Focus prev" },
    { key: "→ / L", action: "Focus next" },
  ],
  ThreeColumn: [
    { key: "← / H", action: "Focus left column" },
    { key: "→ / L", action: "Focus right column" },
    { key: "↑ / K", action: "Focus up in column" },
    { key: "↓ / J", action: "Focus down in column" },
  ],
};

export function KeyboardPanel() {
  const layout = useWindowStore((s) => s.layout);
  const focusShortcuts = FOCUS_SHORTCUTS[layout];

  return (
    <div
      data-testid="keyboard-panel"
      className="flex h-full w-56 flex-shrink-0 flex-col border-l border-border bg-bg-card"
    >
      <div className="border-b border-border px-3 py-2">
        <h2 className="text-xs font-bold uppercase tracking-wider text-text-muted">
          Keyboard
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        {/* Focus section — changes per layout */}
        <div className="mb-3">
          <p className="mb-1.5 px-1 text-[10px] font-semibold uppercase tracking-wider text-accent-light">
            Navigate
          </p>
          {focusShortcuts.map(({ key, action }) => (
            <ShortcutRow key={key} shortcutKey={key} action={action} />
          ))}
        </div>

        {/* Common shortcuts */}
        <div>
          <p className="mb-1.5 px-1 text-[10px] font-semibold uppercase tracking-wider text-accent-light">
            Actions
          </p>
          {COMMON_SHORTCUTS.map(({ key, action }) => (
            <ShortcutRow key={key} shortcutKey={key} action={action} />
          ))}
        </div>
      </div>
    </div>
  );
}

function ShortcutRow({
  shortcutKey,
  action,
}: {
  shortcutKey: string;
  action: string;
}) {
  return (
    <div className="flex items-center justify-between gap-1 rounded px-1 py-0.5">
      <kbd className="min-w-[3.5rem] rounded bg-bg-tertiary px-1.5 py-0.5 text-center font-mono text-[10px] text-accent-light">
        {shortcutKey}
      </kbd>
      <span className="text-right text-[10px] text-text-secondary">
        {action}
      </span>
    </div>
  );
}
