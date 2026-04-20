"use client";

import type { ConjointWidget } from "@/lib/types";

export function ConjointCards({
  widget,
  onSubmit,
  disabled,
}: {
  widget: ConjointWidget;
  onSubmit: (struct: { chosen_alt_index: number }) => void;
  disabled?: boolean;
}) {
  const choose = (idx: number) => {
    if (disabled) return;
    onSubmit({ chosen_alt_index: idx });
  };

  return (
    <div className="rounded-xl border border-darpan-border bg-darpan-surface p-5">
      <div className="mb-4 text-sm text-neutral-300">{widget.scenario}</div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {widget.alternatives.map((alt) => (
          <button
            key={alt.alt_index}
            onClick={() => choose(alt.alt_index)}
            disabled={disabled}
            className="flex flex-col gap-2 rounded-lg border border-darpan-border bg-darpan-elevated p-4 text-left transition hover:border-darpan-lime hover:shadow-glow-lime disabled:opacity-40"
          >
            <div className="text-xs font-mono uppercase tracking-widest text-darpan-lime">{alt.label}</div>
            <ul className="flex flex-col gap-1 text-sm text-neutral-200">
              {Object.entries(alt.display).map(([k, v]) => (
                <li key={k} className="flex items-center justify-between">
                  <span className="text-neutral-500">{prettyKey(k)}</span>
                  <span className="text-right text-neutral-100">{v}</span>
                </li>
              ))}
            </ul>
            <div className="mt-2 text-xs text-neutral-500">Click to pick this one</div>
          </button>
        ))}
      </div>
      {widget.include_none && (
        <div className="mt-3 text-right">
          <button
            onClick={() => choose(-1)}
            disabled={disabled}
            className="rounded-md border border-darpan-border px-3 py-1.5 text-xs text-neutral-400 hover:border-darpan-border-active hover:text-neutral-200 disabled:opacity-40"
          >
            None of these
          </button>
        </div>
      )}
    </div>
  );
}

function prettyKey(k: string): string {
  return k
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace("Usd", "USD")
    .replace("Ram Gb", "RAM (GB)")
    .replace("Battery Hours", "Battery (hr)")
    .replace("Weight Kg", "Weight (kg)")
    .replace("Unit Price", "Unit price")
    .replace("Support Sla", "Support SLA");
}
