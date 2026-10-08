import { Dashboard } from "@/components/dashboard/dashboard";
import { getDashboardData, parseFilters } from "@/lib/analytics";
import { ensureSeeded } from "@/lib/seed";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  // Server-render the default view (last 90 days, all segments) for a fast first paint.
  await ensureSeeded();
  const initialData = await getDashboardData(parseFilters(new URLSearchParams()));

  return <Dashboard initialData={initialData} />;
}
