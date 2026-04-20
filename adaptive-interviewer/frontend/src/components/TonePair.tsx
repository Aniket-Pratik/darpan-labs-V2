"use client";

import { useState } from "react";
import type { TonePairWidget } from "@/lib/types";

export function TonePair({
  widget,
  onSubmit,
  disabled,
}: {
  widget: TonePairWidget;
  onSubmit: (struct: { chosen_ad_id: string; why_text: string }) => void;
  disabled?: boolean;
}) {
  const [chosen, setChosen] = useState<string | null>(null);
  const [why, setWhy] = useState("");

  const submit = () => {
    if (!chosen || !why.trim() || disabled) return;
    onSubmit({ chosen_ad_id: chosen, why_text: why.trim() });
  };

  const ads = [widget.ad_a, widget.ad_b];

  return (
    <div className="rounded-xl border border-darpan-border bg-darpan-surface p-5">
      <div className="mb-4 text-sm text-neutral-300">{widget.prompt}</div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {ads.map((ad) => {
          const active = chosen === ad.id;
          return (
            <button
              key={ad.id}
              onClick={() => setChosen(ad.id)}
              disabled={disabled}
              className={
                "flex flex-col gap-2 rounded-lg border p-4 text-left transition " +
                (active
                  ? "border-darpan-lime bg-darpan-lime/10 shadow-glow-lime"
                  : "border-darpan-border bg-darpan-elevated hover:border-darpan-border-active")
              }
            >
              <div className="text-xs font-mono uppercase tracking-widest text-darpan-lime">Ad {ad.id}</div>
              <div className="text-sm font-semibold text-neutral-100">{ad.label}</div>
              <div className="text-sm leading-relaxed text-neutral-300">{ad.description}</div>
            </button>
          );
        })}
      </div>
      <div className="mt-4">
        <label className="mb-1 block text-xs uppercase tracking-widest text-neutral-500">
          Why? (one sentence is fine)
        </label>
        <textarea
          value={why}
          onChange={(e) => setWhy(e.target.value)}
          disabled={disabled || !chosen}
          rows={2}
          placeholder="Because…"
          className="w-full rounded-lg border border-darpan-border bg-darpan-elevated p-3 text-sm text-neutral-100 outline-none focus:border-darpan-lime disabled:opacity-50"
        />
      </div>
      <div className="mt-3 flex justify-end">
        <button
          onClick={submit}
          disabled={!chosen || !why.trim() || disabled}
          className="rounded-md border border-darpan-lime bg-darpan-lime/15 px-4 py-1.5 text-sm text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
        >
          Submit
        </button>
      </div>
    </div>
  );
}
