"use client";

import { useEffect } from "react";
import type { ContentRow } from "@/lib/types";
import { pad2 } from "@/lib/format";
import { ghostButtonClass, primaryButtonClass } from "./ui";

export function VideoPreviewDialog({ row, onClose }: { row: ContentRow; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  const src = `/api/content/${row.id}/video`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={`Preview of episode ${row.episode}`}
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="dashboard-fade-in flex max-h-[94vh] w-full max-w-md flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl sm:p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              EP {pad2(row.episode)} · {row.collection}
            </p>
            <h2 className="truncate text-sm font-semibold">{row.title}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close preview"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          >
            ✕
          </button>
        </div>

        <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden rounded-xl bg-black">
          {row.hasVideo ? (
            <video
              key={`${row.id}-${row.renderStatus}`}
              src={src}
              controls
              autoPlay
              playsInline
              preload="metadata"
              className="max-h-[70vh] w-auto max-w-full"
              style={{ aspectRatio: "9 / 16" }}
            />
          ) : (
            <p className="p-8 text-center text-sm text-slate-400">No rendered video yet.</p>
          )}
        </div>

        <div className="flex flex-wrap justify-end gap-2">
          {row.hasVideo && (
            <a href={`${src}?download=1`} className={ghostButtonClass}>
              Download MP4
            </a>
          )}
          <button type="button" onClick={onClose} className={primaryButtonClass}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
