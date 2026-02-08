export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface WindowRect {
  id: string;
  rect: Rect;
}

export interface LayoutConfig {
  masterWidth: number; // percentage 0-100
  stackSide: "left" | "right";
  balanceStacks: boolean;
}

export type LayoutName = "MasterStack" | "Autotiling" | "Grid" | "ThreeColumn";

export type LayoutFn = (
  windowIds: string[],
  container: Rect,
  config: LayoutConfig,
) => WindowRect[];
