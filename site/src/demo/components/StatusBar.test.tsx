import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBar } from "./StatusBar";
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

describe("StatusBar", () => {
  beforeEach(resetStore);

  it("renders the status bar", () => {
    render(<StatusBar />);
    expect(screen.getByTestId("status-bar")).toBeInTheDocument();
  });

  it("shows current layout name", () => {
    render(<StatusBar />);
    expect(screen.getByText("MasterStack")).toBeInTheDocument();
  });

  it("shows 0 windows", () => {
    render(<StatusBar />);
    expect(screen.getByText("0 windows")).toBeInTheDocument();
  });

  it("shows 1 window (singular)", () => {
    useWindowStore.getState().spawnWindow();
    render(<StatusBar />);
    expect(screen.getByText("1 window")).toBeInTheDocument();
  });

  it("shows focused window info", () => {
    useWindowStore.getState().spawnWindow();
    render(<StatusBar />);
    expect(screen.getByText("Terminal #1")).toBeInTheDocument();
  });

  it("hides focus info when nothing focused", () => {
    render(<StatusBar />);
    expect(screen.queryByText(/focused/)).not.toBeInTheDocument();
  });
});
