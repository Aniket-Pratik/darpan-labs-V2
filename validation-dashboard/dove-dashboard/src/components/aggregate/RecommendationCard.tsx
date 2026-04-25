import { motion } from 'framer-motion';
import { Trophy, TrendingUp } from 'lucide-react';
import { CONCEPT_COLORS } from '../../constants/theme';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

function composeRecommendation(data: DashboardData): string {
  const topConcept = data.agreement.real_top;
  const best2 = data.real.turf.best_2;
  const realTiers = data.real.tiers;
  const tier1Count = Object.values(realTiers).filter((t) => t === 1).length;
  const hasStatSeparation = tier1Count < Object.keys(realTiers).length;

  if (data.agreement.level === 'Divergent') {
    return `Results diverge between sources. Real favours ${data.agreement.real_top}, twins favour ${data.agreement.twin_top}. Further testing recommended.`;
  }
  if (!hasStatSeparation) {
    return `${topConcept} leads directionally but is not statistically distinguished from other concepts. If developing 2 concepts, ${best2.concepts.join(' + ')} maximises reach at ${best2.reach_pct}%.`;
  }
  if (data.agreement.level === 'Confirmed') {
    return `Lead with ${topConcept}. Optimal 2-concept portfolio: ${best2.concepts.join(' + ')} (${best2.reach_pct}% unduplicated reach).`;
  }
  return `${topConcept} leads with directional agreement. Consider ${best2.concepts.join(' + ')} for maximum reach (${best2.reach_pct}%).`;
}

function t2bColor(v: number): string {
  if (v >= 60) return '#00FF88';
  if (v >= 35) return '#FFB800';
  return '#FF4444';
}

export function RecommendationCard({ data }: Props) {
  const names = Object.keys(data.real.composites)
    .filter((n) => data.real.composites[n] !== null)
    .sort(
      (a, b) => (data.real.composites[b] ?? 0) - (data.real.composites[a] ?? 0),
    );
  const recommended = new Set<string>([data.agreement.real_top]);
  const explanation = composeRecommendation(data);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className="bg-darpan-surface border border-darpan-lime/20 rounded-xl overflow-hidden"
    >
      <div className="flex items-center gap-3 px-5 py-4 border-b border-darpan-border bg-darpan-lime/[0.03]">
        <div className="w-8 h-8 rounded-lg bg-darpan-lime/10 flex items-center justify-center">
          <Trophy className="w-4 h-4 text-darpan-lime" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Recommendation</h3>
          <p className="text-xs text-white/35">
            Based on real customer data, corroborated by twins
          </p>
        </div>
      </div>

      <div className="p-5 space-y-4">
        <p className="text-sm text-white/60 leading-relaxed">{explanation}</p>

        <div className="space-y-2">
          {names.map((name, i) => {
            const isRecommended = recommended.has(name);
            const real = data.real.composites[name] ?? 0;
            const twin = data.twin.composites[name] ?? 0;
            const delta = Math.abs(twin - real);
            const twinDot =
              delta < 5
                ? { color: '#00FF88', label: 'strong' }
                : delta < 10
                  ? { color: '#FFB800', label: 'moderate' }
                  : { color: '#FF4444', label: 'weak' };

            return (
              <div
                key={name}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg ${
                  isRecommended
                    ? 'bg-darpan-lime/[0.06] border border-darpan-lime/15'
                    : 'bg-white/[0.02] border border-transparent'
                }`}
              >
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                    isRecommended
                      ? 'bg-darpan-lime/20 text-darpan-lime'
                      : 'bg-white/5 text-white/30'
                  }`}
                >
                  {i + 1}
                </span>
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: CONCEPT_COLORS[name] || '#A0A0A0' }}
                />
                <span
                  className={`flex-1 text-sm ${isRecommended ? 'text-white font-medium' : 'text-white/40'}`}
                >
                  {name}
                </span>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-3.5 h-3.5" style={{ color: t2bColor(real) }} />
                  <span
                    className="text-sm font-mono tabular-nums font-medium"
                    style={{ color: t2bColor(real) }}
                  >
                    {real.toFixed(1)}%
                  </span>
                </div>
                <div
                  className="flex items-center gap-1 text-[10px] tabular-nums font-mono"
                  style={{ color: twinDot.color }}
                  title={`twin agreement: ${twinDot.label}`}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: twinDot.color }}
                  />
                  {twin.toFixed(1)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
