"use client";

import { useMemo, useState } from "react";
import type { BrandLatticeWidget } from "@/lib/types";

type Responses = Record<string, Record<string, number | "dont_know">>;

export function BrandLattice({
  widget,
  onSubmit,
  disabled,
}: {
  widget: BrandLatticeWidget;
  onSubmit: (struct: { responses: Responses }) => void;
  disabled?: boolean;
}) {
  const [responses, setResponses] = useState<Responses>({});
  const [brandIdx, setBrandIdx] = useState(0);

  const brand = widget.brands[brandIdx];
  const brandResp = responses[brand] || {};
  const scaleVals = useMemo(
    () => Array.from({ length: widget.scale.max - widget.scale.min + 1 }, (_, i) => i + widget.scale.min),
    [widget.scale.max, widget.scale.min],
  );

  const brandComplete = (b: string) =>
    widget.attributes.every((a) => responses[b]?.[a] !== undefined);
  const allDone = widget.brands.every(brandComplete);

  const setCell = (attr: string, v: number | "dont_know") =>
    setResponses((r) => ({ ...r, [brand]: { ...(r[brand] || {}), [attr]: v } }));

  const submit = () => {
    if (!allDone || disabled) return;
    onSubmit({ responses });
  };

  return (
    <div className="rounded-xl border border-darpan-border bg-darpan-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-sm text-neutral-500">Brand {brandIdx + 1} of {widget.brands.length}</div>
          <div className="text-xl font-semibold text-neutral-100">{brand}</div>
        </div>
        <div className="flex gap-1">
          {widget.brands.map((b, i) => (
            <button
              key={b}
              onClick={() => setBrandIdx(i)}
              disabled={disabled}
              className={
                "h-2 w-8 rounded-full " +
                (i === brandIdx
                  ? "bg-darpan-lime"
                  : brandComplete(b)
                  ? "bg-darpan-lime/40"
                  : "bg-darpan-border")
              }
              aria-label={b}
            />
          ))}
        </div>
      </div>

      <ul className="flex flex-col gap-3">
        {widget.attributes.map((attr) => {
          const v = brandResp[attr];
          return (
            <li key={attr} className="flex flex-col gap-1 border-b border-darpan-border/50 pb-2 last:border-none">
              <div className="text-sm text-neutral-200">{attr}</div>
              <div className="flex items-center gap-1">
                {scaleVals.map((n) => {
                  const active = v === n;
                  return (
                    <button
                      key={n}
                      disabled={disabled}
                      onClick={() => setCell(attr, n)}
                      className={
                        "h-8 flex-1 rounded-md border text-xs " +
                        (active
                          ? "border-darpan-lime bg-darpan-lime/20 text-darpan-lime"
                          : "border-darpan-border bg-darpan-elevated text-neutral-500 hover:border-darpan-border-active")
                      }
                    >
                      {n}
                    </button>
                  );
                })}
                {widget.dont_know_escape && (
                  <button
                    disabled={disabled}
                    onClick={() => setCell(attr, "dont_know")}
                    className={
                      "ml-1 h-8 rounded-md border px-2 text-xs " +
                      (v === "dont_know"
                        ? "border-neutral-500 bg-neutral-700 text-neutral-100"
                        : "border-darpan-border bg-darpan-elevated text-neutral-500 hover:border-darpan-border-active")
                    }
                  >
                    Don't know
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      <div className="mt-4 flex items-center justify-between">
        <button
          onClick={() => setBrandIdx((i) => Math.max(0, i - 1))}
          disabled={brandIdx === 0 || disabled}
          className="rounded-md border border-darpan-border px-3 py-1.5 text-sm text-neutral-400 hover:border-darpan-border-active hover:text-neutral-200 disabled:opacity-40"
        >
          Previous brand
        </button>
        {brandIdx < widget.brands.length - 1 ? (
          <button
            onClick={() => setBrandIdx((i) => Math.min(widget.brands.length - 1, i + 1))}
            disabled={!brandComplete(brand) || disabled}
            className="rounded-md border border-darpan-lime bg-darpan-lime/15 px-4 py-1.5 text-sm text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
          >
            Next brand
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!allDone || disabled}
            className="rounded-md border border-darpan-lime bg-darpan-lime/15 px-4 py-1.5 text-sm text-darpan-lime hover:bg-darpan-lime/25 disabled:opacity-40"
          >
            Submit
          </button>
        )}
      </div>
    </div>
  );
}
