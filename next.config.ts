import type { NextConfig } from "next";

/**
 * The API lives in the FastAPI backend (see backend/). Next.js proxies
 * browser requests so client code only ever uses relative /api/* URLs —
 * no CORS, no localhost hardcoded in the browser bundle.
 *
 * Override with API_ORIGIN_INTERNAL when the backend runs elsewhere
 * (Docker Compose sets it to http://api:8000).
 */
const backendOrigin = process.env.API_ORIGIN_INTERNAL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendOrigin}/api/:path*` }];
  },
};

export default nextConfig;
