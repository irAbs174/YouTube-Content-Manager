import { deleteEpisode, parseEpisodePatch, updateEpisode } from "@/lib/content";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

function parseId(raw: string): number | null {
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : null;
}

/** PATCH /api/content/:id — update status or title. */
export async function PATCH(request: Request, { params }: Ctx) {
  const id = parseId((await params).id);
  if (id === null) return Response.json({ error: "Invalid id" }, { status: 400 });

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const parsed = parseEpisodePatch(body);
  if (!parsed.ok) return Response.json({ error: parsed.error }, { status: 400 });

  try {
    const ok = await updateEpisode(id, parsed.value);
    if (!ok) return Response.json({ error: "Episode not found" }, { status: 404 });
    return Response.json({ ok: true, id });
  } catch (error) {
    console.error("[api/content] update failed", error);
    return Response.json({ error: "Could not update episode" }, { status: 500 });
  }
}

/** DELETE /api/content/:id — remove an episode and its analytics. */
export async function DELETE(_request: Request, { params }: Ctx) {
  const id = parseId((await params).id);
  if (id === null) return Response.json({ error: "Invalid id" }, { status: 400 });

  try {
    const ok = await deleteEpisode(id);
    if (!ok) return Response.json({ error: "Episode not found" }, { status: 404 });
    return Response.json({ ok: true, id });
  } catch (error) {
    console.error("[api/content] delete failed", error);
    return Response.json({ error: "Could not delete episode" }, { status: 500 });
  }
}
