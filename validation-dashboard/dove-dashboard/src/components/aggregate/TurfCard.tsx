import { CONCEPT_COLORS } from '../../constants/theme';
import { useDashboardStore } from '../../store/useDashboardStore';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

export function TurfCard({ data }: Props) {
  const dataSource = useDashboardStore((s) => s.dataSource);
  const block = dataSource === 'twin' ? data.twin : data.real;
  const turf = block.turf;

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-xl p-5">
      <div className="text-xs font-medium uppercase tracking-wider text-white/30 mb-3">
        TURF Analysis
      </div>

      <div className="mb-4">
        <div className="text-xs text-white/60 mb-1">Best 2-Concept Portfolio</div>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {turf.best_2.concepts.map((c, i) => (
            <div key={c} className="flex items-center gap-1">
              {i > 0 && <span className="text-white/40 text-[10px]">+</span>}
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CONCEPT_COLORS[c] || '#A0A0A0' }}
              />
              <span className="text-sm font-semibold text-white">{c}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${turf.best_2.reach_pct}%`,
                backgroundColor: '#C8FF00',
              }}
            />
          </div>
          <span className="font-mono text-sm font-semibold text-darpan-lime tabular-nums">
            {turf.best_2.reach_pct}%
          </span>
        </div>
      </div>

      <div className="mb-4">
        <div className="text-xs text-white/60 mb-1">Best 3-Concept Portfolio</div>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {turf.best_3.concepts.map((c, i) => (
            <div key={c} className="flex items-center gap-1">
              {i > 0 && <span className="text-white/40 text-[10px]">+</span>}
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CONCEPT_COLORS[c] || '#A0A0A0' }}
              />
              <span className="text-xs font-medium text-white">{c}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${turf.best_3.reach_pct}%`,
                backgroundColor: '#00D4FF',
              }}
            />
          </div>
          <span className="font-mono text-sm font-semibold text-darpan-cyan tabular-nums">
            {turf.best_3.reach_pct}%
          </span>
        </div>
      </div>

      <div>
        <div className="text-xs text-white/60 mb-2">Individual PI Reach</div>
        <div className="space-y-1.5">
          {Object.entries(turf.individual_reach)
            .sort(([, a], [, b]) => b - a)
            .map(([name, pct]) => (
              <div key={name} className="flex items-center gap-2">
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: CONCEPT_COLORS[name] || '#A0A0A0' }}
                />
                <span className="text-[10px] text-white/60 w-20 truncate">{name}</span>
                <div className="flex-1 h-1 bg-white/[0.04] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: CONCEPT_COLORS[name] || '#A0A0A0',
                      opacity: 0.6,
                    }}
                  />
                </div>
                <span className="font-mono text-[10px] text-white/60 w-8 text-right tabular-nums">
                  {pct.toFixed(0)}%
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
