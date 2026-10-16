import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DEFAULT_API_ORIGIN = "http://127.0.0.1:8000";

const REQUEST_HOP_BY_HOP_HEADERS = [
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "proxy-connection",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
] as const;

const RESPONSE_HOP_BY_HOP_HEADERS = new Set([
  ...REQUEST_HOP_BY_HOP_HEADERS,
  "content-encoding",
  "set-cookie",
]);

/**
 * Proxy API calls at request time so API_ORIGIN_INTERNAL works in deployments
 * where the backend hostname is only available at runtime (for example Docker
 * Compose's `api` service). Next.js rewrites are baked into the build output,
 * which can otherwise leave production pointing at 127.0.0.1 inside the web
 * container.
 */
async function proxy(request: NextRequest): Promise<Response> {
  const incomingUrl = new URL(request.url);
  const apiOrigin = (process.env.API_ORIGIN_INTERNAL || DEFAULT_API_ORIGIN).replace(/\/+$/, "");
  const upstreamUrl = `${apiOrigin}${incomingUrl.pathname}${incomingUrl.search}`;

  const requestHeaders = new Headers(request.headers);
  for (const header of REQUEST_HOP_BY_HOP_HEADERS) {
    requestHeaders.delete(header);
  }
  // Fetch transparently decompresses upstream responses. Avoid requesting a
  // compressed payload and then forwarding a stale Content-Encoding header.
  requestHeaders.delete("accept-encoding");

  const init: RequestInit = {
    method: request.method,
    headers: requestHeaders,
    cache: "no-store",
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    init.body = await request.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, init);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "unknown upstream error";
    console.error(`[api-proxy] ${request.method} ${incomingUrl.pathname} failed: ${detail}`);
    return Response.json({ error: "API backend is unavailable" }, { status: 502 });
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, name) => {
    if (!RESPONSE_HOP_BY_HOP_HEADERS.has(name.toLowerCase())) {
      responseHeaders.set(name, value);
    }
  });

  // Preserve individual Set-Cookie headers (login/logout rely on these). The
  // fallback supports runtimes whose Headers implementation lacks getSetCookie.
  const headersWithCookies = upstream.headers as Headers & {
    getSetCookie?: () => string[];
  };
  const cookies = headersWithCookies.getSetCookie?.();
  if (cookies?.length) {
    for (const cookie of cookies) responseHeaders.append("set-cookie", cookie);
  } else {
    const cookie = upstream.headers.get("set-cookie");
    if (cookie) responseHeaders.set("set-cookie", cookie);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export {
  proxy as DELETE,
  proxy as GET,
  proxy as HEAD,
  proxy as OPTIONS,
  proxy as PATCH,
  proxy as POST,
  proxy as PUT,
};
