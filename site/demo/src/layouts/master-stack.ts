import type { LayoutFn } from "./types";

export const masterStack: LayoutFn = (windowIds, container, config) => {
  if (windowIds.length === 0) return [];

  const { x, y, width, height } = container;
  const masterFrac = config.masterWidth / 100;

  if (windowIds.length === 1) {
    return [{ id: windowIds[0], rect: { x, y, width, height } }];
  }

  const masterW = Math.round(width * masterFrac);
  const stackW = width - masterW;
  const stackCount = windowIds.length - 1;
  const stackH = Math.round(height / stackCount);

  const masterX = config.stackSide === "right" ? x : x + stackW;
  const stackX = config.stackSide === "right" ? x + masterW : x;

  const result = [
    {
      id: windowIds[0],
      rect: { x: masterX, y, width: masterW, height },
    },
  ];

  for (let i = 0; i < stackCount; i++) {
    const isLast = i === stackCount - 1;
    const sy = y + i * stackH;
    const sh = isLast ? height - i * stackH : stackH;
    result.push({
      id: windowIds[i + 1],
      rect: { x: stackX, y: sy, width: stackW, height: sh },
    });
  }

  return result;
};
