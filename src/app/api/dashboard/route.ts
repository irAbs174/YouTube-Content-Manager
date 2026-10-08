import { getDashboardData, parseFilters } from "@/lib/analytics";
import { ensureSeeded } from "@/lib/seed";

export const dynamic = "force-dynamic";

/** GET /api/dashboard?from=YYYY-MM-DD&to=YYYY-MM-DD&collection=All&status=All */
export async function GET(request: Request) {
  try {
    await ensureSeeded();
    const filters = parseFilters(new URL(request.url).searchParams);
    const data = await getDashboardData(filters);
    return Response.json(data, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("[api/dashboard] failed", error);
    return Response.json({ error: "Failed to load dashboard data" }, { status: 500 });
  }
}
