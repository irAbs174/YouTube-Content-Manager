import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { Readable } from "node:stream";
import { eq } from "drizzle-orm";
import { db } from "@/db";
import { youtubeContent } from "@/db/schema";
import { videoAbsPath } from "@/lib/render/storage";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * GET /api/content/:id/video — streams the rendered MP4 with HTTP Range support
 * (so the browser can seek). Add ?download=1 to force a file download.
 */
export async function GET(request: Request, { params }: Ctx) {
  const id = Number((await params).id);
  if (!Number.isInteger(id) || id <= 0) return new Response("Invalid id", { status: 400 });

  const [row] = await db
    .select({ videoPath: youtubeContent.videoPath })
    .from(youtubeContent)
    .where(eq(youtubeContent.id, id))
    .limit(1);
  if (!row?.videoPath) return new Response("No rendered video", { status: 404 });

  const file = videoAbsPath(row.videoPath);
  let size: number;
  try {
    size = (await stat(file)).size;
  } catch {
    return new Response("Video file missing", { status: 404 });
  }

  const url = new URL(request.url);
  const headers: Record<string, string> = {
    "Content-Type": "video/mp4",
    "Accept-Ranges": "bytes",
    "Cache-Control": "no-cache",
  };
  if (url.searchParams.get("download") === "1") {
    headers["Content-Disposition"] = `attachment; filename="episode-${id}.mp4"`;
  }

  const range = request.headers.get("range");
  if (range) {
    const match = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
    if (!match || (match[1] === "" && match[2] === "")) {
      return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
    }
    let start: number;
    let end: number;
    if (match[1] === "") {
      // Suffix range: last N bytes.
      start = Math.max(0, size - Number(match[2]));
      end = size - 1;
    } else {
      start = Number(match[1]);
      end = match[2] === "" ? size - 1 : Math.min(Number(match[2]), size - 1);
    }
    if (start > end || start >= size) {
      return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
    }
    const stream = Readable.toWeb(createReadStream(file, { start, end })) as unknown as BodyInit;
    return new Response(stream, {
      status: 206,
      headers: {
        ...headers,
        "Content-Range": `bytes ${start}-${end}/${size}`,
        "Content-Length": String(end - start + 1),
      },
    });
  }

  const stream = Readable.toWeb(createReadStream(file)) as unknown as BodyInit;
  return new Response(stream, { headers: { ...headers, "Content-Length": String(size) } });
}
