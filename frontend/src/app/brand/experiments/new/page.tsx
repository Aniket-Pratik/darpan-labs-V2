'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Users, FlaskConical, CheckCircle } from 'lucide-react';
import { getUserIdFromStorage } from '@/lib/interviewApi';
import { createExperiment, listCohorts, pollExperimentUntilDone } from '@/lib/experimentApi';
import { CohortBuilder, ScenarioEditor, ResultsDashboard } from '@/components/experiment';
import type { Cohort, CohortCreateResponse, ExperimentScenario, ExperimentResults, ExperimentStatus } from '@/types/experiment';

type Step = 'cohort' | 'scenario' | 'running' | 'results';

export default function NewExperimentPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string>('');
  const [step, setStep] = useState<Step>('cohort');
  const [existingCohorts, setExistingCohorts] = useState<Cohort[]>([]);
  const [selectedCohortId, setSelectedCohortId] = useState<string | null>(null);
  const [selectedCohortSize, setSelectedCohortSize] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progress, setProgress] = useState<ExperimentStatus | null>(null);
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const hasFetched = useRef(false);

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    const uid = getUserIdFromStorage();
    if (!uid) {
      router.push('/create/modules');
      return;
    }
    setUserId(uid);

    listCohorts(uid)
      .then(setCohorts)
      .catch(() => {});
  }, [router]);

  const setCohorts = (cohorts: Cohort[]) => {
    setExistingCohorts(cohorts);
  };

  const handleCohortCreated = (cohort: CohortCreateResponse) => {
    setSelectedCohortId(cohort.id);
    setSelectedCohortSize(cohort.twin_count);
    setStep('scenario');
  };

  const handleSelectExistingCohort = (cohort: Cohort) => {
    setSelectedCohortId(cohort.id);
    setSelectedCohortSize(cohort.twin_ids.length);
    setStep('scenario');
  };

  const handleRunExperiment = async (name: string, scenario: ExperimentScenario) => {
    if (!selectedCohortId) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await createExperiment(userId, {
        name,
        cohort_id: selectedCohortId,
        scenario,
      });

      setStep('running');
      setIsSubmitting(false);

      const finalResults = await pollExperimentUntilDone(
        response.experiment_id,
        (status) => setProgress(status),
        2000
      );

      setResults(finalResults);
      setStep('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create experiment');
      setIsSubmitting(false);
    }
  };

  const stepLabels: Record<Step, string> = {
    cohort: 'Select Cohort',
    scenario: 'Define Scenario',
    running: 'Running...',
    results: 'Results',
  };

  return (
    <div>
      {/* Header */}
      <div className="border-b border-darpan-border">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => step === 'results' ? router.push('/brand/experiments') : router.back()}
            className="flex items-center gap-2 text-white/50 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-lg font-bold text-white">New Experiment</h1>
          <div className="w-16" />
        </div>
      </div>

      {/* Step indicator */}
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="flex items-center gap-2 mb-8">
          {(['cohort', 'scenario', 'running', 'results'] as Step[]).map((s, i) => {
            const isActive = s === step;
            const isPast =
              ['cohort', 'scenario', 'running', 'results'].indexOf(s) <
              ['cohort', 'scenario', 'running', 'results'].indexOf(step);
            return (
              <div key={s} className="flex items-center gap-2 flex-1">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    isActive
                      ? 'bg-darpan-lime text-black'
                      : isPast
                      ? 'bg-darpan-lime/20 text-darpan-lime'
                      : 'bg-darpan-surface text-white/30'
                  }`}
                >
                  {isPast ? <CheckCircle className="w-3.5 h-3.5" /> : i + 1}
                </div>
                <span
                  className={`text-xs hidden sm:inline ${
                    isActive ? 'text-white' : 'text-white/30'
                  }`}
                >
                  {stepLabels[s]}
                </span>
                {i < 3 && (
                  <div
                    className={`flex-1 h-px ${
                      isPast ? 'bg-darpan-lime/30' : 'bg-darpan-border'
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Step content */}
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Step 1: Cohort selection */}
          {step === 'cohort' && (
            <div className="space-y-8">
              {existingCohorts.length > 0 && (
                <section>
                  <h3 className="flex items-center gap-2 text-white font-semibold mb-3">
                    <Users className="w-5 h-5" />
                    Use Existing Cohort
                  </h3>
                  <div className="grid gap-2 mb-4">
                    {existingCohorts.map((cohort) => (
                      <button
                        key={cohort.id}
                        onClick={() => handleSelectExistingCohort(cohort)}
                        className="flex items-center justify-between p-3 bg-darpan-surface border border-darpan-border
                                 rounded-lg hover:border-darpan-lime/30 transition-colors text-left"
                      >
                        <div>
                          <p className="text-white font-medium">{cohort.name}</p>
                          <p className="text-xs text-white/40">{cohort.twin_ids.length} twins</p>
                        </div>
                        <ArrowLeft className="w-4 h-4 text-white/20 rotate-180" />
                      </button>
                    ))}
                  </div>

                  <div className="flex items-center gap-4 my-6">
                    <div className="flex-1 h-px bg-darpan-border" />
                    <span className="text-xs text-white/30">or create new</span>
                    <div className="flex-1 h-px bg-darpan-border" />
                  </div>
                </section>
              )}

              <section>
                <h3 className="flex items-center gap-2 text-white font-semibold mb-3">
                  <Users className="w-5 h-5 text-darpan-lime" />
                  {existingCohorts.length > 0 ? 'Create New Cohort' : 'Build Your Cohort'}
                </h3>
                <CohortBuilder userId={userId} onCohortCreated={handleCohortCreated} />
              </section>
            </div>
          )}

          {/* Step 2: Scenario editor */}
          {step === 'scenario' && (
            <div>
              <div className="flex items-center gap-2 mb-6 p-3 bg-darpan-surface border border-darpan-border rounded-lg">
                <Users className="w-4 h-4 text-darpan-lime" />
                <span className="text-sm text-white/70">
                  Cohort selected: {selectedCohortSize} twins
                </span>
                <button
                  onClick={() => setStep('cohort')}
                  className="ml-auto text-xs text-darpan-lime hover:text-darpan-lime/80"
                >
                  Change
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
                  {error}
                </div>
              )}

              <ScenarioEditor onSubmit={handleRunExperiment} isSubmitting={isSubmitting} />
            </div>
          )}

          {/* Step 3: Running */}
          {step === 'running' && (
            <div className="text-center py-12">
              <motion.div
                className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-r from-darpan-lime/20 to-darpan-cyan/20
                         flex items-center justify-center"
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
              >
                <FlaskConical className="w-10 h-10 text-darpan-lime" />
              </motion.div>

              <h3 className="text-xl font-bold text-white mb-2">Running Experiment</h3>
              <p className="text-white/50 mb-6">
                Processing {selectedCohortSize} twins...
              </p>

              {progress && (
                <div className="max-w-xs mx-auto">
                  <div className="flex justify-between text-sm text-white/50 mb-2">
                    <span>{progress.completed_responses} completed</span>
                    <span>{progress.progress_pct}%</span>
                  </div>
                  <div className="h-2 bg-darpan-surface rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-darpan-lime to-darpan-cyan"
                      animate={{ width: `${progress.progress_pct}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Results */}
          {step === 'results' && results && (
            <ResultsDashboard results={results} />
          )}
        </motion.div>
      </div>
    </div>
  );
}
