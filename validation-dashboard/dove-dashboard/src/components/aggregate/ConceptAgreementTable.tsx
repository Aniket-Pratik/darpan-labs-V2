import { motion } from 'framer-motion';
import { CONCEPT_COLORS } from '../../constants/theme';
import { useDashboardStore } from '../../store/useDashboardStore';
import type { DashboardData } from '../../types';

function bucketFor(absDelta: number): { label: string; color: string } {
  if (absDelta < 5) return { label: 'strong', color: '#00FF88' };
  if (absDelta < 10) return { label: 'moderate', color: '#FFB800' };
  return { label: 'weak', color: '#FF4444' };
}

function deltaBg(absDelta: number): string {
  if (absDelta < 5) return 'rgba(0,255,136,0.10)';
  if (absDelta < 10) return 'rgba(255,184,0,0.10)';
  return 'rgba(255,68,68,0.10)';
}

function t2bBg(v: number | null): string {
  if (v === null) return 'transparent';
  if (v >= 60) return 'rgba(0,255,136,0.12)';
  if (v >= 35) return 'rgba(255,184,0,0.12)';
  return 'rgba(255,68,68,0.12)';
}

interface Props {
  data: DashboardData;
}

export function ConceptAgreementTable({ data }: Props) {
  const dataSource = useDashboardStore((s) => s.dataSource);

  const names = Object.keys(data.real.composites)
    .filter((n) => data.real.composites[n] !== null)
    .sort(
      (a, b) => (data.real.composites[b] ?? 0) - (data.real.composites[a] ?? 0),
    );

  const realDim = dataSource === 'twin' ? 'opacity-30' : '';
  const twinDim = dataSource === 'real' ? 'opacity-30' : '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="bg-darpan-surface border border-darpan-border rounded-xl overflow-hidden"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-darpan-border bg-darpan-bg/50">
              <th className="px-5 py-3.5 text-left text-xs font-medium text-white/40 uppercase tracking-wider">
                Concept
              </th>
              <th
                className={`px-4 py-3.5 text-center text-xs font-medium text-white/40 uppercase tracking-wider ${realDim}`}
              >
                Real
              </th>
              <th
                className={`px-4 py-3.5 text-center text-xs font-medium text-white/40 uppercase tracking-wider ${twinDim}`}
              >
                Twin
              </th>
              <th className="px-4 py-3.5 text-center text-xs font-medium text-white/40 uppercase tracking-wider">
                Δ
              </th>
              <th className="px-4 py-3.5 text-center text-xs font-medium text-white/40 uppercase tracking-wider">
                Agreement
              </th>
            </tr>
          </thead>
          <tbody>
            {names.map((name, i) => {
              const real = data.real.composites[name] ?? 0;
              const twin = data.twin.composites[name] ?? 0;
              const delta = twin - real;
              const bucket = bucketFor(Math.abs(delta));
              return (
                <tr
                  key={name}
                  className={`border-b border-darpan-border/50 ${i % 2 === 0 ? '' : 'bg-white/[0.01]'}`}
                >
                  <td className="px-5 py-3 text-sm font-medium text-white/80">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: CONCEPT_COLORS[name] || '#A0A0A0' }}
                      />
                      {name}
                    </div>
                  </td>
                  <td
                    className={`px-4 py-3 text-center text-sm font-mono tabular-nums text-white ${realDim}`}
                    style={{ backgroundColor: t2bBg(real) }}
                  >
                    {real.toFixed(1)}%
                  </td>
                  <td
                    className={`px-4 py-3 text-center text-sm font-mono tabular-nums text-white ${twinDim}`}
                    style={{ backgroundColor: t2bBg(twin) }}
                  >
                    {twin.toFixed(1)}%
                  </td>
                  <td
                    className="px-4 py-3 text-center text-sm font-mono tabular-nums text-white"
                    style={{ backgroundColor: deltaBg(Math.abs(delta)) }}
                  >
                    {delta >= 0 ? '+' : ''}
                    {delta.toFixed(1)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div
                      className="inline-flex items-center gap-1.5 text-xs"
                      style={{ color: bucket.color }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ backgroundColor: bucket.color }}
                      />
                      {bucket.label}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-5 px-5 py-3 border-t border-darpan-border text-[11px] text-white/30 flex-wrap">
        <span>Δ = twin − real (pp)</span>
        <span className="text-white/10">|</span>
        <span className="flex items-center gap-1.5">
          <span
            className="w-2.5 h-2.5 rounded-sm"
            style={{ backgroundColor: 'rgba(0,255,136,0.3)' }}
          />
          strong &lt;5
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="w-2.5 h-2.5 rounded-sm"
            style={{ backgroundColor: 'rgba(255,184,0,0.3)' }}
          />
          moderate 5–10
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="w-2.5 h-2.5 rounded-sm"
            style={{ backgroundColor: 'rgba(255,68,68,0.3)' }}
          />
          weak &gt;10
        </span>
      </div>
    </motion.div>
  );
}
