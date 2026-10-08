import { inArray } from "drizzle-orm";
import { db } from "@/db";
import { youtubeContent } from "@/db/schema";
import type { RenderState, RenderStatus } from "@/lib/types";

export const dynamic = "force-dynamic";

/**
 * GET /api/renders?ids=1,2,3 — lightweight render-state poll used by the dashboard
 * while jobs are queued or running (avoids refetching the whole dashboard).
 */
export async function GET(request: Request) {
  const ids = (new URL(request.url).searchParams.get("ids") ?? "")
    .split(",")
    .map(Number)
    .filter((n) => Number.isInteger(n) && n > 0)
    .slice(0, 50);
  if (ids.length === 0) return Response.json([]);

  const rows = await db
    .select({
      id: youtubeContent.id,
      renderStatus: youtubeContent.renderStatus,
      renderProgress: youtubeContent.renderProgress,
      renderError: youtubeContent.renderError,
      videoPath: youtubeContent.videoPath,
    })
    .from(youtubeContent)
    .where(inArray(youtubeContent.id, ids));

  const body: RenderState[] = rows.map((r) => ({
    id: r.id,
    renderStatus: r.renderStatus as RenderStatus,
    renderProgress: r.renderProgress,
    renderError: r.renderError ?? null,
    hasVideo: r.videoPath !== null,
  }));
  return Response.json(body, { headers: { "Cache-Control": "no-store" } });
}
