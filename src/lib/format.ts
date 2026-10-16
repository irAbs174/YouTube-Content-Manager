const integerFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const compactFormat = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const percentFormat = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 1,
});

export function fmtInt(value: number): string {
  return integerFormat.format(value);
}

export function fmtCompact(value: number): string {
  return compactFormat.format(value);
}

export function fmtHours(value: number): string {
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value)}h`;
}

export function fmtPct(value: number): string {
  return percentFormat.format(value);
}

export function fmtDuration(seconds: number): string {
  const wholeSeconds = Math.max(0, Math.floor(seconds));
  return `${Math.floor(wholeSeconds / 60)}:${pad2(wholeSeconds % 60)}`;
}

export function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function shorten(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value;
  if (maxLength <= 1) return "…".slice(0, maxLength);
  return `${value.slice(0, maxLength - 1).trimEnd()}…`;
}