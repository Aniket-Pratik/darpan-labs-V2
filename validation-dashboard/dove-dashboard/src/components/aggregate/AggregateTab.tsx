import { motion } from 'framer-motion';
import { DataSourceToggle } from '../shared/DataSourceToggle';
import { ResearchQuestionCard } from './ResearchQuestionCard';
import { HeroVerdictCard } from './HeroVerdictCard';
import { ConceptAgreementTable } from './ConceptAgreementTable';
import { RecommendationCard } from './RecommendationCard';
import { DiagnosticSection } from './DiagnosticSection';
import { TurfCard } from './TurfCard';
import { OrderBiasCard } from './OrderBiasCard';
import { QualitativeInsightsCard } from './QualitativeInsightsCard';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

const DEFAULT_RESEARCH_QUESTION =
  'Which body-wash concept resonates most with Indian women aged 25–45?';

export function AggregateTab({ data }: Props) {
  return (
    <div className="max-w-5xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      <ResearchQuestionCard question={DEFAULT_RESEARCH_QUESTION} />

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.03 }}
        className="flex justify-end"
      >
        <DataSourceToggle />
      </motion.div>

      <HeroVerdictCard data={data} />
      <ConceptAgreementTable data={data} />
      <RecommendationCard data={data} />
      <DiagnosticSection data={data} />

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        <h3 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-3">
          Deep insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TurfCard data={data} />
          <OrderBiasCard data={data} />
          <QualitativeInsightsCard data={data} />
        </div>
      </motion.div>
    </div>
  );
}
