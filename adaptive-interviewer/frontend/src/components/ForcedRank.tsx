"use client";

import { useMemo, useState } from "react";
import type { RankWidget } from "@/lib/types";

export function ForcedRank({
  widget,
  onSubmit,
  disabled,
}: {
  widget: RankWidget;
  onSubmit: (struct: { ranking: string[] }) => void;
  disabled?: boolean;
}) {
  const [ranking, setRanking] = useState<string[]>([]);

  const available = useMemo(
    () => widget.adjectives.filter((a) => !ranking.includes(a)),
    [widget.adjectives, ranking],
  );

  const add = (adj: string) => {
    if (disabled) return;
    if (ranking.length >= widget.top_n) return;
    setRanking((r) => [...r, adj]);
  };
  const removeAt = (idx: number) => {
    if (disabled) return;
    setRanking((r) => r.filter((_, i) => i !== idx));
  };
  const moveUp = (idx: number) => {
    if (disabled || idx === 0) return;
    setRanking((r) => {
      const next = [...r];
      [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
      return next;
    });
  };
  const moveDown = (idx: number) => {
    if (disabled) return;
    setRanking((r) => {
      if (idx >= r.length - 1) return r;
      const next = [...r];
      [next[idx + 1], next[idx]] = [next[idx], next[idx + 1]];
      return next;
    });
  };

  const done = ranking.length === widget.top_n;

  return (
    <div className="rounded-xl border border-darpan-border bg-darpan-surface p-5">
      <div className="mb-4 text-sm text-neutral-300">
        Pick your top {widget.top_n}, in order. You can reorder after picking.
      </div>

      <div className="mb-4">
        <div className="mb-2 text-xs uppercase tracking-widest text-darpan-lime">Your ranking</div>
        <ol className="flex flex-col gap-2">
          {ranking.length === 0 && (
            <li className="text-sm text-neutral-500">Pick words from below.</li>
          )}
          {ranking.map((adj, i) => (
            <li key={adj} className="flex items-center justify-between rounded-md border border-darpan-lime/40 bg-darpan-lime/10 px-3 py-2">
              <span className="flex items-center gap-3 text-sm text-neutral-100">
                <span className="font-mono text-xs text-darpan-lime">#{i + 1}</span>
                <span>{adj}</span>
              </span>
              <span className="flex gap-1">
                <button disabled={disabled || i === 0} onClick={() => moveUp(i)} className="rounded border border-darpan-border px-2 text-xs text-neutral-400 hover:border-darpan-border-active disabled:opacity-40">↑</button>
                <button disabled={disabled || i === ranking.length - 1} onClick={() => moveDown(i)} className="rounded border border-darpan-border px-2 text-xs text-neutral-400 hover:border-darpan-border-active disabled:opacity-40">↓</button>
                <button disabled={disabled} onClick={() => removeAt(i)} className="rounded border border-darpan-border px-2 text-xs text-neutral-400 hover:border-darpan-border-active disabled:opacity-40">✕</button>
              </span>
            </li>
          ))}
        </ol>
      </div>

      <div className="mb-4">
        <div className="mb-2 text-xs uppercase tracking-widest text-neutral-500">Available words</div>
        <div className="flex flex-wrap gap-2">
          {available.map((adj) => (
            <button
              key={adj}
              disabled={disabled || ranking.length >= widget.top_n}
              onClick={() => add(adj)}
              className="rounded-full border border-darpan-border bg-darpan-elevated px-3 py-1.5 text-sm text-neutral-300 hover:border-darpan-lime hover:text-darpan-lime disabled:opacity-40"
            >
              {adj}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => done && onSubmit({ ranking })}
          disabled={!done || disabled}
          className="rounded-md border border-darpan-lime bg-darpan-lime/15 px-4 py-1.5 text-sm text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
        >
          Submit ranking
        </button>
      </div>
    </div>
  );
}
