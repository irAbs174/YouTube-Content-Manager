"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { LibraryRow, PlaceColumn, PlaceOptions } from "@/lib/library-types";
import { cellPayload, displayCell, isBlank, optionLabel } from "@/lib/library";
import { STATUS_COLORS } from "@/lib/constants";

interface PlaceTableProps {
  columns: PlaceColumn[];
  rows: LibraryRow[];
  options: PlaceOptions;
  onPatch: (rowId: number, payload: Record<string, unknown>) => void;
  busyRowId?: number | null;
  emptyMessage?: string;
}

const TEXT_EDITABLE = new Set(["text", "date", "number"]);

export function PlaceTable({
  columns,
  rows,
  options,
  onPatch,
  busyRowId = null,
  emptyMessage = "No rows yet.",
}: PlaceTableProps) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed p-8 text-center text-sm text-slate-500 dark:border-slate-800">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-800 dark:bg-slate-900">
      <table className="min-w-full text-xs">
        <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 dark:bg-slate-800">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="whitespace-nowrap px-3 py-2 text-left font-semibold">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              className={`border-t hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
                busyRowId === row.id ? "opacity-60" : ""
              }`}
            >
              {columns.map((column) => (
                <td key={column.key} className="px-3 py-1.5 align-middle">
                  <Cell
                    row={row}
                    column={column}
                    options={options}
                    onPatch={onPatch}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Cell({
  row,
  column,
  options,
  onPatch,
}: {
  row: LibraryRow;
  column: PlaceColumn;
  options: PlaceOptions;
  onPatch: (rowId: number, payload: Record<string, unknown>) => void;
}) {
  const value = row[column.key];

  if (column.type === "bool") {
    if (!column.editable) {
      return <span className="text-center">{value ? "✓" : "—"}</span>;
    }
    return (
      <label className="flex cursor-pointer items-center gap-1.5">
        <input
          type="checkbox"
          className="h-3.5 w-3.5 accent-slate-900 dark:accent-white"
          checked={Boolean(value)}
          onChange={(event) =>
            onPatch(row.id, cellPayload(column, event.target.checked))
          }
        />
        <span className="text-[10px] text-slate-400">{value ? "yes" : "no"}</span>
      </label>
    );
  }

  if (column.type === "select") {
    const options_ = selectOptions(column, options);
    if (!column.editable) {
      // The Main library's Episode cell is a jump-link to the Lab.
      if (column.key === "episodeId") {
        return (
          <Link
            href={`/lab/${row.id}`}
            className="font-medium text-slate-900 underline-offset-2 hover:underline dark:text-slate-100"
          >
            {optionLabel(options, column.source, value) || "—"}
          </Link>
        );
      }
      return <span>{displayCell(row, column, options)}</span>;
    }
    return (
      <select
        aria-label={`${column.label} — row ${row.id}`}
        className="w-full max-w-[220px] cursor-pointer rounded border border-slate-200 bg-white px-1.5 py-1 text-[11px] font-medium outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
        style={
          column.source === "statuses" && value
            ? { color: STATUS_COLORS[String(value)] }
            : undefined
        }
        value={value === null || value === undefined ? "" : String(value)}
        onChange={(event) =>
          onPatch(row.id, cellPayload(column, event.target.value))
        }
      >
        <option value="">—</option>
        {options_.map((option) => (
          <option key={String(option.value)} value={String(option.value)}>
            {option.label}
          </option>
        ))}
      </select>
    );
  }

  if (column.type === "count") {
    return <span className="text-center tabular-nums">{String(value ?? 0)}</span>;
  }

  if (column.type === "number") {
    if (!column.editable) {
      return <span className="tabular-nums">{String(value ?? 0)}</span>;
    }
    return (
      <input
        type="number"
        aria-label={`${column.label} — row ${row.id}`}
        className="w-20 rounded border border-slate-200 bg-white px-1.5 py-1 text-[11px] outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
        value={value === null || value === undefined ? "" : String(value)}
        onChange={(event) => onPatch(row.id, cellPayload(column, event.target.value))}
      />
    );
  }

  if (!column.editable) {
    return (
      <span className="block max-w-[320px] truncate" title={String(value ?? "")}>
        {displayCell(row, column, options)}
      </span>
    );
  }

  return <EditableText row={row} column={column} onPatch={onPatch} />;
}

function selectOptions(
  column: PlaceColumn,
  options: PlaceOptions,
): { value: string | number; label: string }[] {
  const source = column.source;
  if (source === "statuses") {
    return options.statuses.map((status) => ({ value: status, label: status }));
  }
  if (source === "assetTypes") {
    return options.assetTypes.map((type) => ({ value: type, label: type }));
  }
  if (source === "collectionTypes") {
    return options.collectionTypes.map((type) => ({ value: type, label: type }));
  }
  const list = (options as unknown as Record<string, { id: number; label: string }[]>)[source ?? ""] ?? [];
  return list.map((item) => ({ value: item.id, label: item.label }));
}

/** Click-to-edit text cell (commit on blur or Enter, cancel on Escape). */
function EditableText({
  row,
  column,
  onPatch,
}: {
  row: LibraryRow;
  column: PlaceColumn;
  onPatch: (rowId: number, payload: Record<string, unknown>) => void;
}) {
  const initial = row[column.key];
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(initial === null || initial === undefined ? "" : String(initial));
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  function commit() {
    setEditing(false);
    if (String(draft) === String(initial ?? "")) return;
    onPatch(row.id, cellPayload(column, draft));
  }

  function cancel() {
    setDraft(initial === null || initial === undefined ? "" : String(initial));
    setEditing(false);
  }

  if (!editing) {
    const text = isBlank(initial) ? "—" : String(initial);
    return (
      <button
        type="button"
        title={text}
        onClick={() => {
          setDraft(text === "—" ? "" : text);
          setEditing(true);
        }}
        className="block max-w-[320px] truncate text-left hover:text-slate-900 dark:hover:text-white"
      >
        {text}
      </button>
    );
  }

  const shared =
    "w-full max-w-[320px] rounded border border-slate-300 bg-white px-1.5 py-1 text-[11px] outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-600 dark:bg-slate-900";

  if (column.type === "date") {
    return (
      <input
        ref={inputRef as React.RefObject<HTMLInputElement>}
        type="date"
        className={shared}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === "Enter") commit();
          if (event.key === "Escape") cancel();
        }}
      />
    );
  }

  return (
    <textarea
      ref={inputRef as React.RefObject<HTMLTextAreaElement>}
      rows={1}
      className={`${shared} resize-y`}
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          commit();
        }
        if (event.key === "Escape") cancel();
      }}
    />
  );
}
