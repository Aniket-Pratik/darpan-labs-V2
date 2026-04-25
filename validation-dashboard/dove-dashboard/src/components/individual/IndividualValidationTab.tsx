import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useValidationStore } from '../../store/useValidationStore';
import { ParticipantConceptSelector } from './ParticipantConceptSelector';
import { HeroFidelityCard } from './HeroFidelityCard';
import { AccuracyCard } from './AccuracyCard';
import { RadarChartOverlay } from './RadarChartOverlay';
import { DeviationBarChart } from './DeviationBarChart';
import { AggregateMatrix } from './AggregateMatrix';
import { AggregateSummaryCards } from './AggregateSummaryCards';
import { qualityTier } from '../../lib/validation-utils';
import type {
  IndividualValidationData,
  ConceptValidation,
  PerMetricEntry,
} from '../../types/individual';

interface Props {
  data: IndividualValidationData;
}

function aggregateConcepts(concepts: ConceptValidation[]): ConceptValidation | null {
  const valid = concepts.filter((c) => c.mae !== null);
  if (valid.length === 0) return null;

  const mae = valid.reduce((s, c) => s + (c.mae ?? 0), 0) / valid.length;
  const acc = valid.reduce((s, c) => s + (c.plus_minus_1_accuracy ?? 0), 0) / valid.length;
  const exact = valid.reduce((s, c) => s + (c.exact_match_rate ?? 0), 0) / valid.length;

  const allKeys = new Set<string>();
  valid.forEach((c) => {
    Object.keys(c.real_metrics).forEach((k) => allKeys.add(k));
    Object.keys(c.twin_metrics).forEach((k) => allKeys.add(k));
  });

  const realMetrics: Record<string, number> = {};
  const twinMetrics: Record<string, number> = {};
  const perMetric: PerMetricEntry[] = [];
  for (const key of allKeys) {
    const realVals = valid.map((c) => c.real_metrics[key]).filter((v) => v !== undefined);
    const twinVals = valid.map((c) => c.twin_metrics[key]).filter((v) => v !== undefined);
    if (realVals.length > 0 && twinVals.length > 0) {
      const rAvg = Math.round((realVals.reduce((a, b) => a + b, 0) / realVals.length) * 10) / 10;
      const tAvg = Math.round((twinVals.reduce((a, b) => a + b, 0) / twinVals.length) * 10) / 10;
      realMetrics[key] = rAvg;
      twinMetrics[key] = tAvg;
      perMetric.push({
        metric: key,
        real: rAvg,
        twin: tAvg,
        diff: Math.round((tAvg - rAvg) * 10) / 10,
      });
    }
  }

  return {
    concept_idx: -1,
    concept_name: 'All Concepts',
    real_metrics: realMetrics,
    twin_metrics: twinMetrics,
    mae: Math.round(mae * 100) / 100,
    plus_minus_1_accuracy: Math.round(acc * 10) / 10,
    exact_match_rate: Math.round(exact * 10) / 10,
    per_metric: perMetric,
    quality: {
      mae: qualityTier(mae, 'mae') as 'Good' | 'Acceptable' | 'Poor',
      accuracy: qualityTier(acc, 'accuracy') as 'Good' | 'Acceptable' | 'Poor',
      exact: qualityTier(exact, 'exact') as 'Good' | 'Acceptable' | 'Poor',
    },
    n_metrics: perMetric.length,
  };
}

export function IndividualValidationTab({ data }: Props) {
  const { selectedParticipant, selectedConcept } = useValidationStore();
  const pair = data.pairs.find((p) => p.participant_id === selectedParticipant);

  const concept = useMemo(() => {
    if (!pair) return null;
    if (selectedConcept === -1) return aggregateConcepts(pair.concepts);
    return pair.concepts[selectedConcept] ?? null;
  }, [pair, selectedConcept]);

  const conceptNameForHero =
    selectedConcept === -1 ? null : (concept?.concept_name ?? null);

  return (
    <div className="max-w-5xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <ParticipantConceptSelector data={data} />
      </motion.div>

      {pair && concept ? (
        <>
          <HeroFidelityCard
            participantId={pair.participant_id}
            conceptName={conceptNameForHero}
            concept={concept}
          />

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-3 gap-3"
          >
            <AccuracyCard metricType="mae" value={concept.mae} quality={concept.quality.mae} />
            <AccuracyCard
              metricType="accuracy"
              value={concept.plus_minus_1_accuracy}
              quality={concept.quality.accuracy}
            />
            <AccuracyCard
              metricType="exact"
              value={concept.exact_match_rate}
              quality={concept.quality.exact}
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-3"
          >
            <RadarChartOverlay concept={concept} />
            <DeviationBarChart perMetric={concept.per_metric} />
          </motion.div>
        </>
      ) : (
        <div className="bg-darpan-surface border border-darpan-border rounded-xl p-8 text-center text-white/30 text-sm">
          No data available for this selection.
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="space-y-3"
      >
        <div>
          <h3 className="text-sm font-semibold text-white">Across all participants</h3>
          <p className="text-xs text-white/35 mt-0.5">
            17 × 5 fidelity matrix — click a cell to jump to that pair.
          </p>
        </div>
        <AggregateSummaryCards data={data} />
        <AggregateMatrix data={data} />
      </motion.div>
    </div>
  );
}
