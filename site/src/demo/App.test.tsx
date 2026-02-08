import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App", () => {
  it("renders the title", () => {
    render(<App />);
    expect(screen.getByText("Interactive Demo")).toBeInTheDocument();
  });

  it("renders the layout switcher", () => {
    render(<App />);
    expect(screen.getByTestId("layout-switcher")).toBeInTheDocument();
  });

  it("renders the demo container", () => {
    render(<App />);
    expect(screen.getByTestId("demo-container")).toBeInTheDocument();
  });

  it("renders the status bar", () => {
    render(<App />);
    expect(screen.getByTestId("status-bar")).toBeInTheDocument();
  });
});
