import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Window } from "./Window";
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

const mockWindow = {
  id: "win-1",
  number: 1,
  appName: "Terminal",
  imageIndex: 1,
};
const mockRect = { x: 0, y: 0, width: 500, height: 600 };

describe("Window", () => {
  beforeEach(resetStore);

  it("renders with test id", () => {
    render(
      <Window
        window={mockWindow}
        rect={mockRect}
        containerWidth={1000}
        containerHeight={600}
      />,
    );
    expect(screen.getByTestId("window-win-1")).toBeInTheDocument();
  });

  it("shows the window number", () => {
    render(
      <Window
        window={mockWindow}
        rect={mockRect}
        containerWidth={1000}
        containerHeight={600}
      />,
    );
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("shows the app name", () => {
    render(
      <Window
        window={mockWindow}
        rect={mockRect}
        containerWidth={1000}
        containerHeight={600}
      />,
    );
    expect(screen.getByText("Terminal")).toBeInTheDocument();
  });

  it("clicking the window focuses it", () => {
    render(
      <Window
        window={mockWindow}
        rect={mockRect}
        containerWidth={1000}
        containerHeight={600}
      />,
    );
    fireEvent.click(screen.getByTestId("window-win-1"));
    expect(useWindowStore.getState().focusedId).toBe("win-1");
  });

  it("renders with correct positioning style", () => {
    render(
      <Window
        window={mockWindow}
        rect={mockRect}
        containerWidth={1000}
        containerHeight={600}
      />,
    );
    const el = screen.getByTestId("window-win-1");
    expect(el.style.left).toBe("0%");
    expect(el.style.top).toBe("0%");
    expect(el.style.width).toBe("50%");
    expect(el.style.height).toBe("100%");
  });
});
