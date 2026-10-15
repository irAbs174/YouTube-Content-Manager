import { Dashboard } from "@/components/dashboard/dashboard";
import { fetchInitialDashboard } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  // Server-render the default view (last 90 days, all segments) against the
  // FastAPI backend. If the backend is down we still render the shell and
  // the client retries immediately (ssrFailed skips the first-fetch skip).
  const { data, failed } = await fetchInitialDashboard();

  return <Dashboard initialData={data} ssrFailed={failed} />;
}
