import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWindowStore } from "../store/window-store";

export function LayoutToast() {
  const toast = useWindowStore((s) => s.layoutToast);
  const layout = useWindowStore((s) => s.layout);
  const dismiss = useWindowStore((s) => s.dismissToast);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(dismiss, 3000);
    return () => clearTimeout(timer);
  }, [toast, dismiss]);

  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          key={layout}
          data-testid="layout-toast"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.2 }}
          className="pointer-events-none absolute bottom-4 left-1/2 z-50 -translate-x-1/2"
        >
          <div className="rounded-lg border border-border bg-bg-card/95 px-4 py-2 shadow-xl backdrop-blur-sm">
            <p className="whitespace-nowrap text-xs">
              <span className="font-bold text-accent-light">{layout}</span>
              <span className="mx-2 text-text-muted">—</span>
              <span className="text-text-secondary">{toast}</span>
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
