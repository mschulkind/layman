import { DemoContainer } from "./components/DemoContainer";
import { StatusBar } from "./components/StatusBar";
import { LayoutSwitcher } from "./components/LayoutSwitcher";
import { HelpOverlay } from "./components/HelpOverlay";
import { useKeyboard } from "./hooks/use-keyboard";

export default function App() {
  useKeyboard();

  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center gap-4 p-6">
      <div className="text-center">
        <h1 className="mb-1 text-2xl font-bold text-text-primary">
          <span className="bg-gradient-to-r from-accent to-[#8b5cf6] bg-clip-text text-transparent">
            Layman
          </span>{" "}
          Interactive Demo
        </h1>
        <p className="text-sm text-text-muted">
          Press{" "}
          <kbd className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-xs text-accent-light">
            ?
          </kbd>{" "}
          for keyboard shortcuts
        </p>
      </div>
      <LayoutSwitcher />
      <DemoContainer />
      <StatusBar />
      <HelpOverlay />
    </div>
  );
}
