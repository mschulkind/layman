import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { DemoContainer } from "./DemoContainer";
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

describe("DemoContainer", () => {
  beforeEach(resetStore);

  it("renders the container", () => {
    render(<DemoContainer />);
    expect(screen.getByTestId("demo-container")).toBeInTheDocument();
  });

  it("shows empty state when no windows", () => {
    render(<DemoContainer />);
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });

  it("hides empty state when windows exist", () => {
    useWindowStore.getState().spawnWindow();
    render(<DemoContainer />);
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("renders windows", () => {
    useWindowStore.getState().spawnWindow();
    render(<DemoContainer />);
    expect(screen.getByTestId("window-win-1")).toBeInTheDocument();
  });
});
