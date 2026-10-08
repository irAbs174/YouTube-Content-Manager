"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "yt-master-theme";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggle() {
    const next = !dark;
    const root = document.documentElement;
    // Brief colour cross-fade so the switch feels smooth rather than instant.
    root.classList.add("theme-animating");
    root.classList.toggle("dark", next);
    try {
      localStorage.setItem(STORAGE_KEY, next ? "dark" : "light");
    } catch {
      /* storage unavailable — theme still applies for this session */
    }
    setDark(next);
    window.setTimeout(() => root.classList.remove("theme-animating"), 400);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      title={dark ? "Light mode" : "Dark mode"}
      className="group relative inline-flex h-9 w-16 items-center rounded-full border border-slate-200 bg-slate-100 p-1 transition-colors hover:border-slate-300 focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/25 dark:border-slate-700 dark:bg-slate-800"
    >
      <span
        className={`flex h-7 w-7 items-center justify-center rounded-full bg-white text-amber-500 shadow-md transition-transform duration-300 dark:bg-slate-950 dark:text-indigo-300 ${
          dark ? "translate-x-7" : "translate-x-0"
        }`}
        aria-hidden
      >
        {dark ? (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
          </svg>
        ) : (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </svg>
        )}
      </span>
    </button>
  );
}
