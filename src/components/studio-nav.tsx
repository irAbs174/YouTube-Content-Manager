"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ThemeToggle } from "./dashboard/theme-toggle";
import { logout } from "@/lib/auth";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/lab", label: "Lab" },
  { href: "/emulator", label: "Emulator" },
  { href: "/library", label: "Library" },
];

export function StudioNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setEmail(data?.email ?? null))
      .catch(() => setEmail(null));
  }, [pathname]);

  async function handleLogout() {
    await logout();
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-sm font-bold tracking-tight">
            YTCM Studio
          </Link>
          <nav className="hidden gap-1 sm:flex">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href)) ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          {email && <span className="hidden text-xs text-slate-500 sm:inline">{email}</span>}
          <ThemeToggle />
          {email ? (
            <button onClick={handleLogout} className="rounded-full border px-3 py-1.5 text-xs font-medium hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">
              Logout
            </button>
          ) : (
            <Link href="/login" className="rounded-full bg-slate-900 px-3 py-1.5 text-xs font-medium text-white dark:bg-white dark:text-slate-900">
              Sign in
            </Link>
          )}
        </div>
      </div>
      <div className="flex gap-1 overflow-x-auto px-4 pb-2 sm:hidden">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium ${pathname === item.href ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            {item.label}
          </Link>
        ))}
      </div>
    </header>
  );
}
