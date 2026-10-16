export const STATUSES = [
  "Draft",
  "Scripting",
  "Recording",
  "Editing",
  "Scheduled",
  "Published",
] as const;

export type Status = (typeof STATUSES)[number];

export const STATUS_COLORS: Record<string, string> = {
  Draft: "#94a3b8",
  Scripting: "#f59e0b",
  Recording: "#06b6d4",
  Editing: "#a855f7",
  Scheduled: "#3b82f6",
  Published: "#10b981",
};

interface CollectionOption {
  name: string;
  color: string;
  sounds: string[];
}

export const COLLECTIONS: CollectionOption[] = [
  { name: "Linux Basics", color: "#10b981", sounds: ["Ubuntu Ambience", "Lo-fi Terminal", "Tux Groove"] },
  { name: "Network Hacking", color: "#06b6d4", sounds: ["Synthwave Packet", "Dark Modem", "Port Scan Pulse"] },
  { name: "Privilege Escalation", color: "#f59e0b", sounds: ["Rootkit Riddim", "Sudo Steps", "Kernel Bass"] },
  { name: "OSINT", color: "#8b5cf6", sounds: ["Quiet Investigation", "Archive Dust", "Signal Trace"] },
  { name: "Scripting & Automation", color: "#f43f5e", sounds: ["Bash Beats", "Cron Groove", "Pipe Funk"] },
];

export const EFFECT_OPTIONS = [
  "Glitch strips",
  "Neon glow",
  "Terminal scanlines",
  "Typewriter cursor",
  "Chromatic aberration",
  "Particle rain",
  "CRT curvature",
] as const;

export const SUBTITLE_OPTIONS = ["None", "EN", "EN + ES", "EN + FR", "Auto captions"] as const;
export const LIVE_INTERVAL_MS = 15_000;

export type Preset = "7D" | "30D" | "90D" | "180D" | "Custom";

export const PRESET_DAYS: Record<Exclude<Preset, "Custom">, number> = {
  "7D": 7,
  "30D": 30,
  "90D": 90,
  "180D": 180,
};

export function collectionColor(name: string): string {
  return COLLECTIONS.find((collection) => collection.name === name)?.color ?? "#94a3b8";
}