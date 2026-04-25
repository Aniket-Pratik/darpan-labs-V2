import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import {
  individualHeadline,
  individualSupporting,
  type QualityTier,
} from '../../lib/verdict-utils';
import type { ConceptValidation } from '../../types/individual';

const TIER_CONFIG: Record<QualityTier, { color: string; Icon: typeof CheckCircle2 }> = {
  Good: { color: '#00FF88', Icon: CheckCircle2 },
  Acceptable: { color: '#FFB800', Icon: AlertTriangle },
  Poor: { color: '#FF4444', Icon: XCircle },
};

const TIER_ORDER: QualityTier[] = ['Good', 'Acceptable', 'Poor'];

function worstTier(q: { mae: QualityTier; accuracy: QualityTier; exact: QualityTier }): QualityTier {
  const idx = Math.max(
    TIER_ORDER.indexOf(q.mae),
    TIER_ORDER.indexOf(q.accuracy),
    TIER_ORDER.indexOf(q.exact),
  );
  return TIER_ORDER[idx];
}

interface Props {
  participantId: string;
  conceptName: string | null;
  concept: ConceptValidation;
}

export function HeroFidelityCard({ participantId, conceptName, concept }: Props) {
  const tier = worstTier(concept.quality);
  const cfg = TIER_CONFIG[tier];

  const perMetric = concept.per_metric ?? [];
  const withinOne = perMetric.filter((m) => Math.abs(m.diff) <= 1).length;
  const biggest = perMetric.length
    ? [...perMetric].sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff))[0]
    : null;
  const supporting = individualSupporting({
    withinOneCount: withinOne,
    totalMetrics: perMetric.length,
    largestDeviation: biggest
      ? { metric: biggest.metric.replace(/_/g, ' '), real: biggest.real, twin: biggest.twin }
      : null,
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
              {tier} fidelity
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            {individualHeadline(tier, participantId, conceptName)}
          </h2>
          <p className="text-sm text-white/60 leading-relaxed">{supporting}</p>
        </div>

        <div className="flex flex-col gap-2 shrink-0">
          <div className="bg-white/[0.03] border border-darpan-border rounded-lg px-3 py-2 text-right min-w-[100px]">
            <div className="text-[10px] text-white/30 uppercase tracking-wider">MAE</div>
            <div className="font-mono text-base text-white tabular-nums">
              {concept.mae !== null ? concept.mae.toFixed(2) : '—'}
            </div>
          </div>
          <div className="bg-white/[0.03] border border-darpan-border rounded-lg px-3 py-2 text-right min-w-[100px]">
            <div className="text-[10px] text-white/30 uppercase tracking-wider">±1 acc</div>
            <div className="font-mono text-base text-white tabular-nums">
              {concept.plus_minus_1_accuracy !== null
                ? `${concept.plus_minus_1_accuracy.toFixed(1)}%`
                : '—'}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
