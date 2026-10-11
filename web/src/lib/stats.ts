/** Wilson score interval for k successes in n trials (95%). Matches wfintel.stats.wilson. */
export function wilson(k: number, n: number, z = 1.959964): [number, number] {
  if (n === 0) return [Number.NaN, Number.NaN];
  const p = k / n;
  const d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d;
  const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [Math.max(0, c - h), Math.min(1, c + h)];
}
