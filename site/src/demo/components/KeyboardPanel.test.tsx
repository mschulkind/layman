import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { KeyboardPanel } from "./KeyboardPanel";
import { useWindowStore } from "../store/window-store";

function resetStore() {
  useWindowStore.setState({
    windows: [],
    focusedId: null,
    layout: "MasterStack",
    config: { masterWidth: 50, stackSide: "right", balanceStacks: true },
    showHelp: false,
    nextNumber: 1,
    containerRect: { x: 0, y: 0, width: 1000, height: 600 },
    layoutToast: null,
  });
}

describe("KeyboardPanel", () => {
  beforeEach(resetStore);

  it("is always visible", () => {
    render(<KeyboardPanel />);
    expect(screen.getByTestId("keyboard-panel")).toBeInTheDocument();
  });

  it("shows common shortcuts", () => {
    render(<KeyboardPanel />);
    expect(screen.getByText("Spawn window")).toBeInTheDocument();
    expect(screen.getByText("Close focused")).toBeInTheDocument();
    expect(screen.getByText("Swap with master")).toBeInTheDocument();
  });

  it("shows MasterStack-specific focus descriptions", () => {
    render(<KeyboardPanel />);
    expect(screen.getByText("Focus prev (linear)")).toBeInTheDocument();
    expect(screen.getByText("Focus next (linear)")).toBeInTheDocument();
    expect(screen.getByText("— (no-op)")).toBeInTheDocument();
  });

  it("shows ThreeColumn-specific focus descriptions", () => {
    useWindowStore.setState({ layout: "ThreeColumn" });
    render(<KeyboardPanel />);
    expect(screen.getByText("Focus left column")).toBeInTheDocument();
    expect(screen.getByText("Focus right column")).toBeInTheDocument();
    expect(screen.getByText("Focus up in column")).toBeInTheDocument();
    expect(screen.getByText("Focus down in column")).toBeInTheDocument();
  });

  it("shows Grid-specific focus descriptions", () => {
    useWindowStore.setState({ layout: "Grid" });
    render(<KeyboardPanel />);
    // Grid uses simple prev/next
    const prevTexts = screen.getAllByText("Focus prev");
    expect(prevTexts.length).toBeGreaterThan(0);
  });

  it("has Navigate and Actions sections", () => {
    render(<KeyboardPanel />);
    expect(screen.getByText("Navigate")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
  });
});
