import { DemoContainer } from "./components/DemoContainer";
import { StatusBar } from "./components/StatusBar";
import { LayoutSwitcher } from "./components/LayoutSwitcher";
import { KeyboardPanel } from "./components/KeyboardPanel";
import { useKeyboard } from "./hooks/use-keyboard";

export default function App() {
  useKeyboard();

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden">
      {/* Top bar: title + layout switcher */}
      <div className="flex items-center justify-between border-b border-border bg-bg-card px-4 py-2">
        <h1 className="text-sm font-bold text-text-primary">
          <span className="bg-gradient-to-r from-accent to-[#8b5cf6] bg-clip-text text-transparent">
            Layman
          </span>{" "}
          <span className="text-text-muted">Interactive Demo</span>
        </h1>
        <LayoutSwitcher />
      </div>

      {/* Main area: demo container + keyboard panel sidebar */}
      <div className="flex min-h-0 flex-1">
        {/* Demo container fills remaining space */}
        <div className="flex min-w-0 flex-1 flex-col p-2">
          <DemoContainer />
          <StatusBar />
        </div>

        {/* Always-visible keyboard shortcuts panel */}
        <KeyboardPanel />
      </div>
    </div>
  );
}
