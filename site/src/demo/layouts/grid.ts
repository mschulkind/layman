import type { LayoutFn } from "./types";

export const grid: LayoutFn = (windowIds, container, _config) => {
  if (windowIds.length === 0) return [];

  const { x, y, width, height } = container;
  const n = windowIds.length;

  if (n === 1) {
    return [{ id: windowIds[0], rect: { x, y, width, height } }];
  }

  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  const cellW = Math.round(width / cols);
  const cellH = Math.round(height / rows);

  return windowIds.map((id, i) => {
    const row = Math.floor(i / cols);
    const col = i % cols;
    const isLastRow = row === rows - 1;
    const itemsInRow = isLastRow ? n - row * cols : cols;
    const rowOffset = isLastRow
      ? Math.round((cols - itemsInRow) * cellW / 2)
      : 0;

    return {
      id,
      rect: {
        x: x + col * cellW + rowOffset,
        y: y + row * cellH,
        width: cellW,
        height: isLastRow ? height - row * cellH : cellH,
      },
    };
  });
};
