import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LayoutSwitcher } from "./LayoutSwitcher";
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

describe("LayoutSwitcher", () => {
  beforeEach(resetStore);

  it("renders all 4 layout buttons", () => {
    render(<LayoutSwitcher />);
    expect(screen.getByTestId("layout-btn-MasterStack")).toBeInTheDocument();
    expect(screen.getByTestId("layout-btn-Autotiling")).toBeInTheDocument();
    expect(screen.getByTestId("layout-btn-Grid")).toBeInTheDocument();
    expect(screen.getByTestId("layout-btn-ThreeColumn")).toBeInTheDocument();
  });

  it("clicking a button switches the layout", () => {
    render(<LayoutSwitcher />);
    fireEvent.click(screen.getByTestId("layout-btn-Grid"));
    expect(useWindowStore.getState().layout).toBe("Grid");
  });

  it("active button has distinct styling", () => {
    render(<LayoutSwitcher />);
    const btn = screen.getByTestId("layout-btn-MasterStack");
    expect(btn.className).toContain("bg-accent");
  });

  it("inactive button has transparent background", () => {
    render(<LayoutSwitcher />);
    const btn = screen.getByTestId("layout-btn-Grid");
    expect(btn.className).toContain("bg-transparent");
  });
});
