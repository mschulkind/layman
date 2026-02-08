import type { LayoutFn, Rect, WindowRect } from "./types";

function stackWindows(
  ids: string[],
  rect: Rect,
): WindowRect[] {
  if (ids.length === 0) return [];
  const sliceH = Math.round(rect.height / ids.length);
  return ids.map((id, i) => {
    const isLast = i === ids.length - 1;
    return {
      id,
      rect: {
        x: rect.x,
        y: rect.y + i * sliceH,
        width: rect.width,
        height: isLast ? rect.height - i * sliceH : sliceH,
      },
    };
  });
}

export const threeColumn: LayoutFn = (windowIds, container, config) => {
  if (windowIds.length === 0) return [];

  const { x, y, width, height } = container;
  const masterFrac = config.masterWidth / 100;

  if (windowIds.length === 1) {
    return [{ id: windowIds[0], rect: { x, y, width, height } }];
  }

  if (windowIds.length === 2) {
    const masterW = Math.round(width * masterFrac);
    const stackW = width - masterW;
    return [
      {
        id: windowIds[0],
        rect: { x: x + stackW, y, width: masterW, height },
      },
      {
        id: windowIds[1],
        rect: { x, y, width: stackW, height },
      },
    ];
  }

  // 3+ windows: center master, left stack, right stack
  const masterW = Math.round(width * masterFrac);
  const sideW = Math.round((width - masterW) / 2);
  const rightW = width - masterW - sideW;

  const masterX = x + sideW;

  const stackIds = windowIds.slice(1);
  const leftIds: string[] = [];
  const rightIds: string[] = [];

  stackIds.forEach((id, i) => {
    if (config.balanceStacks) {
      if (i % 2 === 0) {
        leftIds.push(id);
      } else {
        rightIds.push(id);
      }
    } else {
      // Fill left first
      if (leftIds.length <= rightIds.length) {
        leftIds.push(id);
      } else {
        rightIds.push(id);
      }
    }
  });

  const result: WindowRect[] = [
    {
      id: windowIds[0],
      rect: { x: masterX, y, width: masterW, height },
    },
  ];

  result.push(
    ...stackWindows(leftIds, { x, y, width: sideW, height }),
  );
  result.push(
    ...stackWindows(rightIds, {
      x: masterX + masterW,
      y,
      width: rightW,
      height,
    }),
  );

  return result;
};
