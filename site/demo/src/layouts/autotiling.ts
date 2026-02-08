import type { LayoutFn, Rect, WindowRect } from "./types";

function splitRect(
  ids: string[],
  rect: Rect,
  depth: number,
): WindowRect[] {
  if (ids.length === 0) return [];
  if (ids.length === 1) {
    return [{ id: ids[0], rect }];
  }

  const half = Math.ceil(ids.length / 2);
  const first = ids.slice(0, half);
  const second = ids.slice(half);

  const splitVertically = depth % 2 === 0;

  if (splitVertically) {
    const w1 = Math.round(rect.width / 2);
    const w2 = rect.width - w1;
    return [
      ...splitRect(first, { ...rect, width: w1 }, depth + 1),
      ...splitRect(
        second,
        { x: rect.x + w1, y: rect.y, width: w2, height: rect.height },
        depth + 1,
      ),
    ];
  } else {
    const h1 = Math.round(rect.height / 2);
    const h2 = rect.height - h1;
    return [
      ...splitRect(first, { ...rect, height: h1 }, depth + 1),
      ...splitRect(
        second,
        { x: rect.x, y: rect.y + h1, width: rect.width, height: h2 },
        depth + 1,
      ),
    ];
  }
}

export const autotiling: LayoutFn = (windowIds, container, _config) => {
  if (windowIds.length === 0) return [];
  return splitRect(windowIds, container, 0);
};
