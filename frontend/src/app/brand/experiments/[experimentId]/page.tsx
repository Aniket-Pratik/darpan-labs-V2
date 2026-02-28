'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, FlaskConical } from 'lucide-react';
import { getExperimentResults, getExperimentStatus, pollExperimentUntilDone } from '@/lib/experimentApi';
import { ResultsDashboard } from '@/components/experiment';
import type { ExperimentResults, ExperimentStatus } from '@/types/experiment';

export default function ExperimentResultsPage({
  params,
}: {
  params: Promise<{ experimentId: string }>;
}) {
  const { experimentId } = use(params);
  const router = useRouter();
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [progress, setProgress] = useState<ExperimentStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadResults();
  }, [experimentId]);

  const loadResults = async () => {
    try {
      const status = await getExperimentStatus(experimentId);

      if (status.status === 'running') {
        setProgress(status);
        const finalResults = await pollExperimentUntilDone(
          experimentId,
          (s) => setProgress(s),
          2000
        );
        setResults(finalResults);
      } else {
        const data = await getExperimentResults(experimentId);
        setResults(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="border-b border-darpan-border">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => router.push('/brand/experiments')}
            className="flex items-center gap-2 text-white/50 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Experiments
          </button>
          <h1 className="text-lg font-bold text-white">
            {results?.name || 'Experiment Results'}
          </h1>
          <div className="w-16" />
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {isLoading ? (
          <div className="text-center py-16">
            {progress && progress.status === 'running' ? (
              <div>
                <motion.div
                  className="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-500/20 flex items-center justify-center"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                >
                  <FlaskConical className="w-8 h-8 text-blue-400" />
                </motion.div>
                <p className="text-white/70 mb-4">
                  Experiment running... {progress.completed_responses}/{progress.total_twins}
                </p>
                <div className="max-w-xs mx-auto h-2 bg-darpan-surface rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-blue-400"
                    animate={{ width: `${progress.progress_pct}%` }}
                  />
                </div>
              </div>
            ) : (
              <Loader2 className="w-12 h-12 text-darpan-lime animate-spin mx-auto" />
            )}
          </div>
        ) : error ? (
          <div className="text-center py-16">
            <p className="text-red-400">{error}</p>
            <button
              onClick={() => router.push('/brand/experiments')}
              className="mt-4 px-4 py-2 bg-white/10 text-white rounded-lg"
            >
              Back to Experiments
            </button>
          </div>
        ) : results ? (
          <ResultsDashboard results={results} />
        ) : null}
      </main>
    </div>
  );
}
