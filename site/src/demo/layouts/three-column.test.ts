import { describe, it, expect } from "vitest";
import { threeColumn } from "./three-column";
import type { LayoutConfig, Rect } from "./types";

const container: Rect = { x: 0, y: 0, width: 1000, height: 600 };
const config: LayoutConfig = {
  masterWidth: 50,
  stackSide: "right",
  balanceStacks: true,
};

describe("threeColumn", () => {
  it("returns empty array for no windows", () => {
    expect(threeColumn([], container, config)).toEqual([]);
  });

  it("single window fills the container", () => {
    const result = threeColumn(["a"], container, config);
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ id: "a", rect: container });
  });

  it("two windows: master + one side", () => {
    const result = threeColumn(["a", "b"], container, config);
    expect(result).toHaveLength(2);
    expect(result[0].rect.width).toBe(500); // master
    expect(result[1].rect.width).toBe(500); // side
  });

  it("three windows: center master + left + right", () => {
    const result = threeColumn(["a", "b", "c"], container, config);
    expect(result).toHaveLength(3);
    // Master should be centered
    const masterRect = result[0].rect;
    expect(masterRect.width).toBe(500);
    expect(masterRect.x).toBe(250); // center
  });

  it("four windows: balanced stacks", () => {
    const result = threeColumn(["a", "b", "c", "d"], container, config);
    expect(result).toHaveLength(4);
    // With balanceStacks, b→left, c→right
    // Master "a" centered, "b" left, "c" right, "d" left
    expect(result[0].id).toBe("a");
  });

  it("five windows distributes evenly", () => {
    const result = threeColumn(
      ["a", "b", "c", "d", "e"],
      container,
      config,
    );
    expect(result).toHaveLength(5);
    for (const wr of result) {
      expect(wr.rect.width).toBeGreaterThan(0);
      expect(wr.rect.height).toBeGreaterThan(0);
    }
  });

  it("respects masterWidth config", () => {
    const wideConfig = { ...config, masterWidth: 60 };
    const result = threeColumn(["a", "b", "c"], container, wideConfig);
    expect(result[0].rect.width).toBe(600);
  });

  it("returns correct ids", () => {
    const result = threeColumn(["x", "y", "z"], container, config);
    const ids = result.map((r) => r.id);
    expect(ids).toContain("x");
    expect(ids).toContain("y");
    expect(ids).toContain("z");
  });
});
