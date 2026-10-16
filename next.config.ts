import type { NextConfig } from "next";

/**
 * Browser API calls use relative /api/* URLs. They are handled by the runtime
 * proxy in src/app/api/[...path]/route.ts so API_ORIGIN_INTERNAL can be supplied
 * at container startup (rather than being baked into the Next.js build).
 */
const nextConfig: NextConfig = {};

export default nextConfig;
