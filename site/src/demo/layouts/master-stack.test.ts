import { describe, it, expect } from "vitest";
import { masterStack } from "./master-stack";
import type { LayoutConfig, Rect } from "./types";

const container: Rect = { x: 0, y: 0, width: 1000, height: 600 };
const config: LayoutConfig = {
  masterWidth: 50,
  stackSide: "right",
  balanceStacks: true,
};

describe("masterStack", () => {
  it("returns empty array for no windows", () => {
    expect(masterStack([], container, config)).toEqual([]);
  });

  it("single window fills the container", () => {
    const result = masterStack(["a"], container, config);
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ id: "a", rect: container });
  });

  it("two windows: master left, stack right", () => {
    const result = masterStack(["a", "b"], container, config);
    expect(result).toHaveLength(2);
    expect(result[0].rect.width).toBe(500);
    expect(result[1].rect.width).toBe(500);
    expect(result[1].rect.x).toBe(500);
  });

  it("three windows: stack splits vertically", () => {
    const result = masterStack(["a", "b", "c"], container, config);
    expect(result).toHaveLength(3);
    expect(result[1].rect.height).toBe(300);
    expect(result[2].rect.height).toBe(300);
    expect(result[2].rect.y).toBe(300);
  });

  it("respects stackSide=left", () => {
    const leftConfig = { ...config, stackSide: "left" as const };
    const result = masterStack(["a", "b"], container, leftConfig);
    expect(result[0].rect.x).toBe(500); // master on right
    expect(result[1].rect.x).toBe(0); // stack on left
  });

  it("respects masterWidth config", () => {
    const wideConfig = { ...config, masterWidth: 70 };
    const result = masterStack(["a", "b"], container, wideConfig);
    expect(result[0].rect.width).toBe(700);
    expect(result[1].rect.width).toBe(300);
  });

  it("handles many windows in stack", () => {
    const ids = ["a", "b", "c", "d", "e"];
    const result = masterStack(ids, container, config);
    expect(result).toHaveLength(5);
    // All stack windows should be at x=500
    for (let i = 1; i < result.length; i++) {
      expect(result[i].rect.x).toBe(500);
    }
  });

  it("all rects cover the full container height", () => {
    const ids = ["a", "b", "c", "d"];
    const result = masterStack(ids, container, config);
    const stackRects = result.slice(1);
    const totalStackH = stackRects.reduce((s, r) => s + r.rect.height, 0);
    expect(totalStackH).toBe(600);
  });
});
