import { addDays, todayISO } from "./dates";
import type { DashboardData, KpiKey } from "./types";
import { cookies } from "next/headers";

const KPI_KEYS: KpiKey[] = ["views", "watchHours", "subs", "ctr", "likes"];

function emptyDashboard(): DashboardData {
  const to = todayISO();
  const from = addDays(to, -89);
  const kpis = Object.fromEntries(KPI_KEYS.map((key) => [key, { value: 0, prev: 0 }])) as DashboardData["kpis"];
  return {
    range: { from, to, days: 90 },
    kpis,
    series: [],
    rows: [],
    generatedAt: new Date().toISOString(),
  };
}

export async function fetchInitialDashboard(): Promise<{ data: DashboardData; failed: boolean }> {
  const origin = process.env.API_ORIGIN_INTERNAL ?? "http://127.0.0.1:8000";
  try {
    // Forward cookies for auth if present
    let cookieHeader = "";
    try {
      const cookieStore = await cookies();
      cookieHeader = cookieStore.toString();
    } catch {
      cookieHeader = "";
    }
    const response = await fetch(`${origin}/api/dashboard`, {
      cache: "no-store",
      headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
    });
    if (!response.ok) throw new Error(`Dashboard request failed (${response.status})`);
    return { data: (await response.json()) as DashboardData, failed: false };
  } catch {
    return { data: emptyDashboard(), failed: true };
  }
}

export async function fetchCurrentUser(): Promise<{ id: number; email: string } | null> {
  const origin = process.env.API_ORIGIN_INTERNAL ?? "http://127.0.0.1:8000";
  try {
    let cookieHeader = "";
    try {
      const cookieStore = await cookies();
      cookieHeader = cookieStore.toString();
    } catch {
      cookieHeader = "";
    }
    const res = await fetch(`${origin}/api/auth/me`, {
      cache: "no-store",
      headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
    });
    if (!res.ok) return null;
    return (await res.json()) as { id: number; email: string };
  } catch {
    return null;
  }
}
