import { createEpisode, parseEpisodeInput } from "@/lib/content";
import { enqueueRender } from "@/lib/render/queue";
import { getFfmpegStatus } from "@/lib/render/ffmpeg";
import { ensureSeeded } from "@/lib/seed";

export const dynamic = "force-dynamic";

/**
 * POST /api/content — create an episode. When `render` is true (default) the
 * episode is queued for FFmpeg rendering and the response returns immediately.
 */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const parsed = parseEpisodeInput(body);
  if (!parsed.ok) return Response.json({ error: parsed.error }, { status: 400 });

  try {
    await ensureSeeded();

    if (parsed.value.render) {
      const ffmpeg = await getFfmpegStatus();
      if (!ffmpeg.available || !ffmpeg.drawtext) {
        return Response.json(
          { error: `${ffmpeg.error ?? "FFmpeg unavailable"} Uncheck "Render video" to save without rendering.` },
          { status: 503 },
        );
      }
    }

    const row = await createEpisode(parsed.value);
    if (parsed.value.render) enqueueRender(row.id);

    return Response.json(
      { ...row, renderStatus: parsed.value.render ? "queued" : "none" },
      { status: 201 },
    );
  } catch (error) {
    console.error("[api/content] create failed", error);
    return Response.json({ error: "Could not create episode" }, { status: 500 });
  }
}


