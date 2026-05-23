export type Category = "A" | "B" | "C" | "D" | "E";

export interface Totals {
  A: number;
  B: number;
  C: number;
  D: number;
  E: number;
  total: number;
  day: string;
}

export interface DetectionEvent {
  id: number;
  ts: string;
  day: string;
  category: Category;
  color_name: string;
}

export interface StatsResponse {
  today: Totals;
  recent: DetectionEvent[];
  live: {
    category: Category;
    color_name: string;
    hue: number;
    saturation: number;
    value: number;
    mean_hsv: [number, number, number];
    mean_rgb_hex: string;
  } | null;
  camera_mode: string;
  inference_ms: number;
  display_fps: number;
}

export interface SystemStats {
  cpu: {
    load_percent: number;
    cores: number;
  };
  gpu: {
    name: string | null;
    temperature_c: number | null;
    level: string;
    load_percent: number | null;
    memory_percent: number | null;
  };
  memory: {
    percent: number;
    used_gb: number;
    total_gb: number;
  };
}

const base = "";

export async function getStats(): Promise<StatsResponse> {
  const r = await fetch(`${base}/api/stats`);
  if (!r.ok) throw new Error("stats failed");
  return r.json();
}

export async function getHistory(start: string, end: string): Promise<{ days: Totals[] }> {
  const r = await fetch(`${base}/api/history?start=${start}&end=${end}`);
  if (!r.ok) throw new Error("history failed");
  return r.json();
}

export async function getSystem(): Promise<SystemStats> {
  const r = await fetch(`${base}/api/system`);
  if (!r.ok) throw new Error("system failed");
  return r.json();
}

export async function sendLine(message: string): Promise<{ delivered: boolean; transport: string }> {
  const r = await fetch(`${base}/api/notify/line`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!r.ok) throw new Error("notify failed");
  return r.json();
}

export interface Settings {
  interval_sec: number;
  allowed_intervals: number[];
  auto_notify: boolean;
  roi_fraction: number;
  paused: boolean;
}

export async function getSettings(): Promise<Settings> {
  const r = await fetch(`${base}/api/settings`);
  if (!r.ok) throw new Error("settings failed");
  return r.json();
}

export async function setInterval_(seconds: number): Promise<void> {
  const r = await fetch(`${base}/api/settings/interval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seconds }),
  });
  if (!r.ok) throw new Error("set interval failed");
}

export async function setAutoNotify(enabled: boolean): Promise<void> {
  const r = await fetch(`${base}/api/settings/auto_notify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!r.ok) throw new Error("set auto_notify failed");
}

export async function setRoi(fraction: number): Promise<void> {
  const r = await fetch(`${base}/api/settings/roi`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fraction }),
  });
  if (!r.ok) throw new Error("set roi failed");
}

export async function resetSettings(): Promise<Settings> {
  const r = await fetch(`${base}/api/settings/reset`, { method: "POST" });
  if (!r.ok) throw new Error("reset settings failed");
  return r.json();
}

export async function setPaused(paused: boolean): Promise<void> {
  const r = await fetch(`${base}/api/settings/pause`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paused }),
  });
  if (!r.ok) throw new Error("pause failed");
}

export async function resetAll(scope: "all" | "today" = "all"): Promise<{ deleted: number }> {
  const r = await fetch(`${base}/api/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scope }),
  });
  if (!r.ok) throw new Error("reset failed");
  return r.json();
}

export function excelUrl(start: string, end: string): string {
  return `${base}/api/export/excel?start=${start}&end=${end}`;
}

export const streamUrl = `${base}/api/camera/stream`;

export function subscribeEvents(onDetection: (e: DetectionEvent) => void): () => void {
  const es = new EventSource(`${base}/api/events`);
  es.addEventListener("detection", (ev) => {
    try {
      onDetection(JSON.parse((ev as MessageEvent).data));
    } catch {
      /* ignore */
    }
  });
  return () => es.close();
}
