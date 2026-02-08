import { describe, it, expect } from "vitest";
import { autotiling } from "./autotiling";
import type { LayoutConfig, Rect } from "./types";

const container: Rect = { x: 0, y: 0, width: 1000, height: 600 };
const config: LayoutConfig = {
  masterWidth: 50,
  stackSide: "right",
  balanceStacks: true,
};

describe("autotiling", () => {
  it("returns empty array for no windows", () => {
    expect(autotiling([], container, config)).toEqual([]);
  });

  it("single window fills the container", () => {
    const result = autotiling(["a"], container, config);
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({ id: "a", rect: container });
  });

  it("two windows split vertically (first split)", () => {
    const result = autotiling(["a", "b"], container, config);
    expect(result).toHaveLength(2);
    expect(result[0].rect.width).toBe(500);
    expect(result[1].rect.width).toBe(500);
    expect(result[1].rect.x).toBe(500);
  });

  it("three windows: left half, then right half splits horizontally", () => {
    const result = autotiling(["a", "b", "c"], container, config);
    expect(result).toHaveLength(3);
    // "a","b" on left half, "c" on right half
    // left half splits horizontally
    expect(result[0].rect.width).toBe(500);
    expect(result[1].rect.width).toBe(500);
  });

  it("four windows creates a 2x2 grid-like pattern", () => {
    const result = autotiling(["a", "b", "c", "d"], container, config);
    expect(result).toHaveLength(4);
    // All windows should have valid rects
    for (const wr of result) {
      expect(wr.rect.width).toBeGreaterThan(0);
      expect(wr.rect.height).toBeGreaterThan(0);
    }
  });

  it("preserves total area across splits", () => {
    const ids = Array.from({ length: 6 }, (_, i) => `w${i}`);
    const result = autotiling(ids, container, config);
    const totalArea = result.reduce(
      (s, r) => s + r.rect.width * r.rect.height,
      0,
    );
    // Should be very close to container area (rounding may cause ±1 per split)
    expect(totalArea).toBeGreaterThan(container.width * container.height * 0.95);
  });

  it("returns correct ids in order", () => {
    const ids = ["x", "y", "z"];
    const result = autotiling(ids, container, config);
    expect(result.map((r) => r.id)).toEqual(["x", "y", "z"]);
  });

  it("handles 8 windows", () => {
    const ids = Array.from({ length: 8 }, (_, i) => `w${i}`);
    const result = autotiling(ids, container, config);
    expect(result).toHaveLength(8);
  });

  it("no windows overlap", () => {
    const ids = Array.from({ length: 5 }, (_, i) => `w${i}`);
    const result = autotiling(ids, container, config);
    for (let i = 0; i < result.length; i++) {
      for (let j = i + 1; j < result.length; j++) {
        const a = result[i].rect;
        const b = result[j].rect;
        const overlapX = a.x < b.x + b.width && a.x + a.width > b.x;
        const overlapY = a.y < b.y + b.height && a.y + a.height > b.y;
        expect(overlapX && overlapY).toBe(false);
      }
    }
  });
});
