import { CONCEPT_COLORS, METRIC_LABELS } from '../../constants/theme';
import type { DashboardData } from '../../types';

const CORE_COLS = ['pi', 'uniqueness', 'relevance', 'believability'] as const;
const EXTRA_COLS = ['interest', 'brand_fit'] as const;

function diffBg(absDelta: number): string {
  if (absDelta < 5) return 'rgba(0,255,136,0.18)';
  if (absDelta < 10) return 'rgba(255,184,0,0.18)';
  return 'rgba(255,68,68,0.18)';
}

function diffColor(absDelta: number): string {
  if (absDelta < 5) return '#00FF88';
  if (absDelta < 10) return '#FFB800';
  return '#FF4444';
}

interface Props {
  data: DashboardData;
}

export function UnifiedDiffHeatmap({ data }: Props) {
  const names = Object.keys(data.real.composites)
    .filter((n) => data.real.composites[n] !== null)
    .sort(
      (a, b) => (data.real.composites[b] ?? 0) - (data.real.composites[a] ?? 0),
    );

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-xl p-4 overflow-x-auto">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
          Δ twin − real (pp)
        </div>
        <div className="flex items-center gap-3 text-[10px] text-white/30">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: diffBg(2) }} />
            |Δ|&lt;5
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: diffBg(7) }} />
            5–10
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: diffBg(15) }} />
            &gt;10
          </span>
        </div>
      </div>

      <div
        className="grid gap-px"
        style={{
          gridTemplateColumns: `140px repeat(${CORE_COLS.length}, 1fr) 8px repeat(${EXTRA_COLS.length}, 1fr)`,
        }}
      >
        <div />
        {CORE_COLS.map((m) => (
          <div key={m} className="text-[10px] text-center text-white/60 pb-2">
            {METRIC_LABELS[m] ?? m}
          </div>
        ))}
        <div />
        {EXTRA_COLS.map((m) => (
          <div key={m} className="text-[10px] text-center text-white/40 pb-2">
            {METRIC_LABELS[m] ?? m}
          </div>
        ))}

        {names.map((name) => (
          <div key={name} className="contents">
            <div className="flex items-center gap-1.5 pr-2 py-2">
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: CONCEPT_COLORS[name] || '#A0A0A0' }}
              />
              <span className="text-xs font-medium text-white truncate">{name}</span>
            </div>
            {CORE_COLS.map((m) => {
              const r = data.real.t2b[name]?.[m]?.t2b ?? null;
              const t = data.twin.t2b[name]?.[m]?.t2b ?? null;
              if (r === null || t === null) {
                return (
                  <div
                    key={m}
                    className="flex items-center justify-center py-2 text-[11px] text-white/20"
                  >
                    —
                  </div>
                );
              }
              const d = t - r;
              return (
                <div
                  key={m}
                  className="flex items-center justify-center py-2 font-mono tabular-nums text-xs"
                  style={{
                    backgroundColor: diffBg(Math.abs(d)),
                    color: diffColor(Math.abs(d)),
                  }}
                  title={`real ${r.toFixed(1)} · twin ${t.toFixed(1)} · Δ ${d.toFixed(1)}`}
                >
                  {d >= 0 ? '+' : ''}
                  {d.toFixed(1)}
                </div>
              );
            })}
            <div className="border-l border-darpan-border" />
            {EXTRA_COLS.map((m) => {
              const r = data.real.t2b[name]?.[m]?.t2b ?? null;
              const t = data.twin.t2b[name]?.[m]?.t2b ?? null;
              if (r === null || t === null) {
                return (
                  <div
                    key={m}
                    className="flex items-center justify-center py-2 text-[11px] text-white/20"
                  >
                    —
                  </div>
                );
              }
              const d = t - r;
              return (
                <div
                  key={m}
                  className="flex items-center justify-center py-2 font-mono tabular-nums text-xs"
                  style={{
                    backgroundColor: diffBg(Math.abs(d)),
                    color: diffColor(Math.abs(d)),
                  }}
                  title={`real ${r.toFixed(1)} · twin ${t.toFixed(1)} · Δ ${d.toFixed(1)}`}
                >
                  {d >= 0 ? '+' : ''}
                  {d.toFixed(1)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
