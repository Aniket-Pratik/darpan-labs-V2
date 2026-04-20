"use client";

export function ProgressBar({
  phase,
  label,
  pct,
}: {
  phase?: string;
  label?: string | null;
  pct?: number;
}) {
  const p = Math.max(0, Math.min(100, pct ?? 0));
  return (
    <div className="flex items-center gap-4 border-b border-darpan-border bg-darpan-surface/60 px-4 py-3">
      <div className="font-mono text-[11px] uppercase tracking-widest text-darpan-lime">
        {phase || "phase —"}
      </div>
      <div className="flex-1">
        <div className="h-1 overflow-hidden rounded-full bg-darpan-border">
          <div className="h-full bg-darpan-lime transition-all" style={{ width: `${p}%` }} />
        </div>
      </div>
      <div className="text-xs text-neutral-500">{label || ""}</div>
    </div>
  );
}
