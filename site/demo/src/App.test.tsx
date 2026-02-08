import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { useWindowStore } from "./store/window-store";

function resetStore() {
  useWindowStore.setState({
    windows: [],
    focusedId: null,
    layout: "MasterStack",
    config: { masterWidth: 50, stackSide: "right", balanceStacks: true },
    showHelp: false,
    nextNumber: 1,
    containerRect: { x: 0, y: 0, width: 1000, height: 600 },
  });
}

describe("App", () => {
  beforeEach(resetStore);

  it("renders the title", () => {
    render(<App />);
    expect(screen.getByText("Interactive Demo")).toBeInTheDocument();
  });

  it("renders the layout switcher", () => {
    render(<App />);
    expect(screen.getByTestId("layout-switcher")).toBeInTheDocument();
  });

  it("renders the status bar", () => {
    render(<App />);
    expect(screen.getByTestId("status-bar")).toBeInTheDocument();
  });

  it("renders the demo container", () => {
    render(<App />);
    expect(screen.getByTestId("demo-container")).toBeInTheDocument();
  });
});
