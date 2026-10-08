import { readFile } from "node:fs/promises";
import { thumbAbsPath } from "@/lib/render/storage";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/** GET /api/content/:id/thumbnail — JPEG frame extracted by FFmpeg after rendering. */
export async function GET(_request: Request, { params }: Ctx) {
  const id = Number((await params).id);
  if (!Number.isInteger(id) || id <= 0) return new Response("Invalid id", { status: 400 });

  try {
    const buf = await readFile(thumbAbsPath(id));
    return new Response(new Uint8Array(buf), {
      headers: { "Content-Type": "image/jpeg", "Cache-Control": "no-cache" },
    });
  } catch {
    return new Response("No thumbnail", { status: 404 });
  }
}
