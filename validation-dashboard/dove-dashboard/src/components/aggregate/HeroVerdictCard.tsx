import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import {
  aggregateHeadline,
  aggregateSupporting,
  spearmanRho,
  overallAgreementPct,
  sharedTierCount,
  type AgreementLevel,
} from '../../lib/verdict-utils';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

const LEVEL_CONFIG: Record<AgreementLevel, { color: string; Icon: typeof CheckCircle2 }> = {
  Confirmed: { color: '#00FF88', Icon: CheckCircle2 },
  Directional: { color: '#FFB800', Icon: AlertTriangle },
  Divergent: { color: '#FF4444', Icon: XCircle },
};

function nonNullScores(m: Record<string, number | null>): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(m)) {
    if (v !== null && v !== undefined) out[k] = v;
  }
  return out;
}

export function HeroVerdictCard({ data }: Props) {
  const level = data.agreement.level as AgreementLevel;
  const cfg = LEVEL_CONFIG[level];

  const realScores = nonNullScores(data.real.composites);
  const twinScores = nonNullScores(data.twin.composites);

  const agreementPct = overallAgreementPct(realScores, twinScores);
  const rho = spearmanRho(realScores, twinScores);
  const shared = sharedTierCount(data.real.tiers, data.twin.tiers);
  const total = Object.keys(data.real.tiers).length;

  const rankAgreement = (() => {
    const names = Object.keys(realScores).filter((n) => n in twinScores);
    const sortedReal = [...names].sort((a, b) => realScores[b] - realScores[a]);
    const sortedTwin = [...names].sort((a, b) => twinScores[b] - twinScores[a]);
    let pairs = 0;
    for (let i = 0; i < names.length; i++) if (sortedReal[i] === sortedTwin[i]) pairs++;
    return pairs;
  })();

  const supporting = aggregateSupporting({
    level,
    realTop: data.agreement.real_top,
    twinTop: data.agreement.twin_top,
    friedmanP: data.real.friedman.p_value ?? 1,
    friedmanSig: data.real.friedman.significant,
    sharedTiers: shared,
    totalConcepts: total,
    rankAgreementPairs: rankAgreement,
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 }}
      className="bg-darpan-surface border border-darpan-border rounded-xl overflow-hidden"
      style={{
        borderLeftWidth: 3,
        borderLeftColor: cfg.color,
        boxShadow: `0 0 20px ${cfg.color}10`,
      }}
    >
      <div className="flex items-start justify-between gap-4 p-5">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <cfg.Icon className="w-4 h-4" style={{ color: cfg.color }} />
            <span
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: cfg.color }}
            >
              {level}
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">{aggregateHeadline(level)}</h2>
          <p className="text-sm text-white/60 leading-relaxed">{supporting}</p>
        </div>

        <div className="flex flex-col gap-2 shrink-0">
          <div className="bg-white/[0.03] border border-darpan-border rounded-lg px-3 py-2 text-right min-w-[100px]">
            <div className="text-[10px] text-white/30 uppercase tracking-wider">Agreement</div>
            <div className="font-mono text-base text-white tabular-nums">{agreementPct}%</div>
          </div>
          <div className="bg-white/[0.03] border border-darpan-border rounded-lg px-3 py-2 text-right min-w-[100px]">
            <div className="text-[10px] text-white/30 uppercase tracking-wider">Rank ρ</div>
            <div className="font-mono text-base text-white tabular-nums">{rho.toFixed(2)}</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
