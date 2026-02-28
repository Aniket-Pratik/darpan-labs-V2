'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  TrendingUp,
  Shield,
  MessageSquare,
} from 'lucide-react';
import type { ExperimentResults, IndividualResult } from '@/types/experiment';
import { CONFIDENCE_COLORS } from '@/types/twin';

interface ResultsDashboardProps {
  results: ExperimentResults;
}

export function ResultsDashboard({ results }: ResultsDashboardProps) {
  const { aggregate_results: agg, individual_results: individuals } = results;
  const [expandedTwin, setExpandedTwin] = useState<string | null>(null);

  // Find the max count for bar chart scaling
  const maxCount = agg
    ? Math.max(...Object.values(agg.choice_distribution).map((d) => d.count), 1)
    : 1;

  return (
    <div className="space-y-8">
      {/* Header stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="Responses"
          value={`${results.completed_responses}/${results.cohort_size}`}
          sub="twins responded"
        />
        <StatCard
          label="Avg Confidence"
          value={agg ? `${Math.round(agg.aggregate_confidence * 100)}%` : '-'}
          sub="across all twins"
        />
        <StatCard
          label="Execution"
          value={results.execution_time_sec ? `${Math.round(results.execution_time_sec)}s` : '-'}
          sub="total time"
        />
      </div>

      {/* Choice distribution */}
      {agg && Object.keys(agg.choice_distribution).length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-white font-semibold mb-4">
            <BarChart3 className="w-5 h-5 text-darpan-lime" />
            Choice Distribution
          </h3>
          <div className="space-y-3">
            {Object.entries(agg.choice_distribution)
              .sort(([, a], [, b]) => b.count - a.count)
              .map(([choice, dist]) => (
                <div key={choice}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-white">{choice}</span>
                    <span className="text-white/50">
                      {dist.count} ({dist.percentage}%)
                    </span>
                  </div>
                  <div className="h-3 bg-darpan-surface rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-darpan-lime to-darpan-cyan rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${(dist.count / maxCount) * 100}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* Confidence distribution */}
      {agg && Object.keys(agg.confidence_distribution).length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-white font-semibold mb-4">
            <Shield className="w-5 h-5 text-darpan-cyan" />
            Confidence Breakdown
          </h3>
          <div className="flex gap-3">
            {['high', 'medium', 'low'].map((level) => {
              const count = agg.confidence_distribution[level] || 0;
              const colors = CONFIDENCE_COLORS[level];
              return (
                <div
                  key={level}
                  className={`flex-1 p-3 rounded-lg border ${colors?.bg || ''} ${colors?.border || 'border-darpan-border'}`}
                >
                  <p className={`text-2xl font-bold ${colors?.text || 'text-white'}`}>{count}</p>
                  <p className="text-xs text-white/40 capitalize">{level}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Key patterns */}
      {agg && agg.key_patterns.length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-white font-semibold mb-4">
            <TrendingUp className="w-5 h-5 text-darpan-lime" />
            Key Patterns
          </h3>
          <div className="space-y-2">
            {agg.key_patterns.map((pattern, i) => (
              <div
                key={i}
                className="p-3 bg-darpan-surface border border-darpan-border rounded-lg"
              >
                <p className="text-sm text-white">{pattern.pattern}</p>
                <div className="flex gap-3 mt-1 text-xs text-white/40">
                  <span>{pattern.supporting_twins} twins</span>
                  <span>{Math.round(pattern.confidence * 100)}% confidence</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Reasoning themes */}
      {agg && agg.dominant_reasoning_themes.length > 0 && (
        <section>
          <h3 className="text-white font-semibold mb-3">Dominant Themes</h3>
          <div className="flex flex-wrap gap-2">
            {agg.dominant_reasoning_themes.map((theme, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-darpan-surface border border-darpan-border rounded-full text-sm text-white/70"
              >
                {theme}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Individual results */}
      <section>
        <h3 className="text-white font-semibold mb-4">
          Individual Responses ({individuals.length})
        </h3>
        <div className="space-y-2">
          {individuals.map((result) => (
            <IndividualResultCard
              key={result.twin_id}
              result={result}
              isExpanded={expandedTwin === result.twin_id}
              onToggle={() =>
                setExpandedTwin(expandedTwin === result.twin_id ? null : result.twin_id)
              }
            />
          ))}
        </div>
      </section>

      {/* Limitations disclaimer */}
      <section className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
        <div className="flex gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-400 mb-1">Limitations</p>
            <p className="text-xs text-white/50">{results.limitations_disclaimer}</p>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="p-4 bg-darpan-surface border border-darpan-border rounded-lg">
      <p className="text-xs text-white/40 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-white/30">{sub}</p>
    </div>
  );
}

function IndividualResultCard({
  result,
  isExpanded,
  onToggle,
}: {
  result: IndividualResult;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const colors = CONFIDENCE_COLORS[result.confidence_label];

  return (
    <div className="bg-darpan-surface border border-darpan-border rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-white/40">
            {result.twin_id.slice(0, 8)}
          </span>
          {result.choice && (
            <span className="px-2 py-0.5 bg-darpan-lime/10 text-darpan-lime text-xs rounded">
              {result.choice}
            </span>
          )}
          <span
            className={`px-2 py-0.5 text-xs rounded ${colors?.bg || ''} ${colors?.text || ''}`}
          >
            {result.confidence_label}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-white/30" />
        ) : (
          <ChevronDown className="w-4 h-4 text-white/30" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 space-y-3 border-t border-darpan-border pt-3">
              {/* Reasoning */}
              <div>
                <p className="text-xs text-white/40 mb-1">Reasoning</p>
                <p className="text-sm text-white/80">{result.reasoning}</p>
              </div>

              {/* Twin info */}
              <div className="flex gap-4 text-xs text-white/40">
                <span>Quality: {result.twin_quality}</span>
                <span>Modules: {result.modules_completed.join(', ')}</span>
                <span>Score: {Math.round(result.confidence_score * 100)}%</span>
              </div>

              {/* Coverage gaps */}
              {result.coverage_gaps.length > 0 && (
                <div>
                  <p className="text-xs text-white/40 mb-1">Coverage Gaps</p>
                  <div className="flex flex-wrap gap-1">
                    {result.coverage_gaps.map((gap, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded"
                      >
                        {gap}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Chat with this twin */}
              <Link
                href={`/brand/chat?twinId=${result.twin_id}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs
                         bg-darpan-cyan/10 text-darpan-cyan border border-darpan-cyan/20
                         rounded-lg hover:bg-darpan-cyan/20 transition-colors"
              >
                <MessageSquare className="w-3 h-3" />
                Chat with this twin
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
