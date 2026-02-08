import { useWindowStore } from "../store/window-store";
import type { LayoutName } from "../layouts/types";

const LAYOUTS: { name: LayoutName; label: string }[] = [
  { name: "MasterStack", label: "MasterStack" },
  { name: "Autotiling", label: "Autotiling" },
  { name: "Grid", label: "Grid" },
  { name: "ThreeColumn", label: "ThreeColumn" },
];

export function LayoutSwitcher() {
  const currentLayout = useWindowStore((s) => s.layout);
  const switchLayout = useWindowStore((s) => s.switchLayout);

  return (
    <div data-testid="layout-switcher" className="flex gap-2">
      {LAYOUTS.map(({ name, label }, index) => (
        <button
          key={name}
          data-testid={`layout-btn-${name}`}
          onClick={() => switchLayout(name)}
          className={`rounded-lg border px-3 py-1.5 font-mono text-xs font-medium transition-all ${
            currentLayout === name
              ? "border-accent bg-accent text-white shadow-[0_0_12px_rgba(99,102,241,0.3)]"
              : "border-border bg-transparent text-text-secondary hover:border-border-hover hover:text-text-primary"
          }`}
        >
          <span className="mr-1.5 text-text-muted">{index + 1}</span>
          {label}
        </button>
      ))}
    </div>
  );
}
