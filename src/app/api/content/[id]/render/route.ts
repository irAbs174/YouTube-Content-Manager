import { requestRender } from "@/lib/render/queue";
import { ensureSeeded } from "@/lib/seed";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/** POST /api/content/:id/render — (re)queue an FFmpeg render for an episode. */
export async function POST(_request: Request, { params }: Ctx) {
  const id = Number((await params).id);
  if (!Number.isInteger(id) || id <= 0) return Response.json({ error: "Invalid id" }, { status: 400 });

  try {
    await ensureSeeded();
    const result = await requestRender(id);
    if (result === "missing") return Response.json({ error: "Episode not found" }, { status: 404 });
    return Response.json({ ok: true, id, renderStatus: "queued" }, { status: result === "queued" ? 202 : 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not queue render";
    const unavailable = /ffmpeg/i.test(message);
    console.error("[api/render] queue failed", error);
    return Response.json({ error: message }, { status: unavailable ? 503 : 500 });
  }
}
