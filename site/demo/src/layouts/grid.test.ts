import { describe, it, expect } from "vitest";
import { grid } from "./grid";
import type { LayoutConfig, Rect } from "./types";

const container: Rect = { x: 0, y: 0, width: 1000, height: 600 };
const config: LayoutConfig = {
  masterWidth: 50,
  stackSide: "right",
  balanceStacks: true,
};

describe("grid", () => {
  it("returns empty array for no windows", () => {
    expect(grid([], container, config)).toEqual([]);
  });

  it("single window fills the container", () => {
    const result = grid(["a"], container, config);
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ id: "a", rect: container });
  });

  it("two windows: 2 columns, 1 row", () => {
    const result = grid(["a", "b"], container, config);
    expect(result).toHaveLength(2);
    expect(result[0].rect.width).toBe(500);
    expect(result[1].rect.width).toBe(500);
    expect(result[1].rect.x).toBe(500);
  });

  it("four windows: 2x2 grid", () => {
    const result = grid(["a", "b", "c", "d"], container, config);
    expect(result).toHaveLength(4);
    expect(result[0].rect).toEqual({ x: 0, y: 0, width: 500, height: 300 });
    expect(result[3].rect).toEqual({
      x: 500,
      y: 300,
      width: 500,
      height: 300,
    });
  });

  it("three windows: 2 cols, 2 rows with last row centered", () => {
    const result = grid(["a", "b", "c"], container, config);
    expect(result).toHaveLength(3);
    // Last row has 1 item, should be offset to center
    expect(result[2].rect.x).toBe(250); // centered offset
  });

  it("nine windows: 3x3 grid", () => {
    const result = grid(
      Array.from({ length: 9 }, (_, i) => `w${i}`),
      container,
      config,
    );
    expect(result).toHaveLength(9);
    const cellW = Math.round(1000 / 3);
    const cellH = Math.round(600 / 3);
    expect(result[0].rect.width).toBe(cellW);
    expect(result[0].rect.height).toBe(cellH);
  });

  it("returns correct ids in order", () => {
    const ids = ["x", "y", "z"];
    const result = grid(ids, container, config);
    expect(result.map((r) => r.id)).toEqual(["x", "y", "z"]);
  });

  it("all rects have positive dimensions", () => {
    const ids = Array.from({ length: 7 }, (_, i) => `w${i}`);
    const result = grid(ids, container, config);
    for (const wr of result) {
      expect(wr.rect.width).toBeGreaterThan(0);
      expect(wr.rect.height).toBeGreaterThan(0);
    }
  });
});
