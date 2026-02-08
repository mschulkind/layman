import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HelpOverlay } from "./HelpOverlay";
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
  });
}

describe("HelpOverlay", () => {
  beforeEach(resetStore);

  it("is hidden when showHelp is false", () => {
    render(<HelpOverlay />);
    expect(screen.queryByTestId("help-overlay")).not.toBeInTheDocument();
  });

  it("is visible when showHelp is true", () => {
    useWindowStore.setState({ showHelp: true });
    render(<HelpOverlay />);
    expect(screen.getByTestId("help-overlay")).toBeInTheDocument();
  });

  it("shows keyboard shortcuts", () => {
    useWindowStore.setState({ showHelp: true });
    render(<HelpOverlay />);
    expect(screen.getByText("Spawn window")).toBeInTheDocument();
    expect(screen.getByText("Close focused window")).toBeInTheDocument();
  });

  it("clicking backdrop closes overlay", () => {
    useWindowStore.setState({ showHelp: true });
    render(<HelpOverlay />);
    fireEvent.click(screen.getByTestId("help-overlay"));
    expect(useWindowStore.getState().showHelp).toBe(false);
  });

  it("clicking inside does not close overlay", () => {
    useWindowStore.setState({ showHelp: true });
    render(<HelpOverlay />);
    const heading = screen.getByText("⌨️ Keyboard Shortcuts");
    fireEvent.click(heading);
    expect(useWindowStore.getState().showHelp).toBe(true);
  });
});
