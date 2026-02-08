import { motion } from "framer-motion";
import type { WindowData } from "../store/window-store";
import { useWindowStore } from "../store/window-store";

interface WindowProps {
  window: WindowData;
  rect: { x: number; y: number; width: number; height: number };
  containerWidth: number;
  containerHeight: number;
}

const WINDOW_COLORS = [
  "from-indigo-500 to-purple-600",
  "from-emerald-500 to-teal-600",
  "from-amber-500 to-orange-600",
  "from-rose-500 to-pink-600",
  "from-cyan-500 to-blue-600",
  "from-violet-500 to-fuchsia-600",
  "from-lime-500 to-green-600",
  "from-red-500 to-rose-600",
  "from-sky-500 to-indigo-600",
  "from-yellow-500 to-amber-600",
];

export function Window({
  window: win,
  rect,
  containerWidth,
  containerHeight,
}: WindowProps) {
  const focusedId = useWindowStore((s) => s.focusedId);
  const focusWindow = useWindowStore((s) => s.focusWindow);
  const isFocused = focusedId === win.id;

  const colorClass = WINDOW_COLORS[(win.number - 1) % WINDOW_COLORS.length];

  const left = (rect.x / containerWidth) * 100;
  const top = (rect.y / containerHeight) * 100;
  const width = (rect.width / containerWidth) * 100;
  const height = (rect.height / containerHeight) * 100;

  const GAP = 3;

  return (
    <motion.div
      data-testid={`window-${win.id}`}
      layout
      layoutId={win.id}
      onClick={() => focusWindow(win.id)}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      className="absolute"
      style={{
        left: `${left}%`,
        top: `${top}%`,
        width: `${width}%`,
        height: `${height}%`,
        padding: `${GAP}px`,
      }}
    >
      <div
        className={`flex h-full w-full flex-col overflow-hidden rounded-lg border transition-all duration-150 ${
          isFocused
            ? "border-accent shadow-[0_0_20px_rgba(99,102,241,0.3)]"
            : "border-border hover:border-border-hover"
        }`}
      >
        <div
          className={`flex items-center gap-2 px-2.5 py-1.5 ${
            isFocused ? "bg-bg-tertiary" : "bg-bg-card"
          }`}
        >
          <div className="flex gap-1">
            <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
            <div className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
            <div className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
          </div>
          <span className="flex-1 truncate text-center font-mono text-[10px] text-text-muted">
            {win.appName}
          </span>
        </div>
        <div
          className={`relative flex flex-1 items-center justify-center bg-gradient-to-br ${colorClass}`}
        >
          <img
            src={`https://placecats.com/${200 + win.imageIndex * 13}/${150 + win.imageIndex * 7}`}
            alt={`Cat ${win.number}`}
            className="absolute inset-0 h-full w-full object-cover opacity-30"
            loading="lazy"
          />
          <span className="relative z-10 text-3xl font-bold text-white drop-shadow-lg">
            {win.number}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
