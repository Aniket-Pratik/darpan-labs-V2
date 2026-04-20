"use client";

import { useMemo, useState } from "react";
import type { SliderBatteryWidget } from "@/lib/types";

export function SliderBattery({
  widget,
  onSubmit,
  disabled,
}: {
  widget: SliderBatteryWidget;
  onSubmit: (struct: { responses: Record<string, number> }) => void;
  disabled?: boolean;
}) {
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [screen, setScreen] = useState(0);

  const screens = useMemo(() => {
    const size = widget.items_per_screen || 10;
    const out: typeof widget.items[] = [];
    for (let i = 0; i < widget.items.length; i += size) {
      out.push(widget.items.slice(i, i + size));
    }
    return out;
  }, [widget.items, widget.items_per_screen]);

  const current = screens[screen];
  const min = widget.scale.min;
  const max = widget.scale.max;
  const minLabel = widget.scale.labels[String(min)] || String(min);
  const maxLabel = widget.scale.labels[String(max)] || String(max);
  const allScreensAnswered =
    screens[screen]?.every((it) => responses[it.n] !== undefined) ?? false;
  const allDone = widget.items.every((it) => responses[it.n] !== undefined);

  const submit = () => {
    if (!allDone || disabled) return;
    const keyed: Record<string, number> = {};
    for (const [k, v] of Object.entries(responses)) keyed[k] = v;
    onSubmit({ responses: keyed });
  };

  return (
    <div className="rounded-xl border border-darpan-border bg-darpan-surface p-5">
      {widget.stem && (
        <div className="mb-3 text-sm font-medium text-neutral-300">{widget.stem}</div>
      )}
      {widget.instruction && (
        <div className="mb-3 text-sm font-medium text-neutral-300">{widget.instruction}</div>
      )}
      <div className="mb-4 flex items-center justify-between text-xs text-neutral-500">
        <span>Screen {screen + 1} of {screens.length}</span>
        <span>{Object.keys(responses).length} of {widget.items.length} answered</span>
      </div>

      <ul className="flex flex-col gap-5">
        {current.map((item) => (
          <li key={item.n} className="flex flex-col gap-2 border-b border-darpan-border/50 pb-3 last:border-none">
            <div className="text-[15px] text-neutral-100">{item.text}</div>
            <div className="flex items-center gap-2 text-xs text-neutral-500">
              <span className="w-32 truncate">{minLabel}</span>
              <div className="flex flex-1 items-center justify-between gap-2">
                {Array.from({ length: max - min + 1 }, (_, i) => i + min).map((v) => {
                  const active = responses[item.n] === v;
                  return (
                    <button
                      key={v}
                      disabled={disabled}
                      onClick={() => setResponses((r) => ({ ...r, [item.n]: v }))}
                      className={
                        "h-9 flex-1 rounded-md border text-sm transition " +
                        (active
                          ? "border-darpan-lime bg-darpan-lime/20 text-darpan-lime"
                          : "border-darpan-border bg-darpan-elevated text-neutral-400 hover:border-darpan-border-active hover:text-neutral-200")
                      }
                    >
                      {v}
                    </button>
                  );
                })}
              </div>
              <span className="w-32 truncate text-right">{maxLabel}</span>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-4 flex items-center justify-between">
        <button
          className="rounded-md border border-darpan-border px-3 py-1.5 text-sm text-neutral-400 hover:border-darpan-border-active hover:text-neutral-200 disabled:opacity-40"
          onClick={() => setScreen((s) => Math.max(0, s - 1))}
          disabled={screen === 0 || disabled}
        >
          Back
        </button>
        {screen < screens.length - 1 ? (
          <button
            className="rounded-md border border-darpan-lime bg-darpan-lime/15 px-4 py-1.5 text-sm text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
            onClick={() => setScreen((s) => Math.min(screens.length - 1, s + 1))}
            disabled={!allScreensAnswered || disabled}
          >
            Next screen
          </button>
        ) : (
          <button
            className="rounded-md border border-darpan-lime bg-darpan-lime/15 px-4 py-1.5 text-sm text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
            onClick={submit}
            disabled={!allDone || disabled}
          >
            Submit
          </button>
        )}
      </div>
      {widget.citation && (
        <div className="mt-3 text-[11px] text-neutral-600">{widget.citation}</div>
      )}
    </div>
  );
}
