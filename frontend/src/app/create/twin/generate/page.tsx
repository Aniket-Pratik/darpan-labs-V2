'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Sparkles, Loader2, CheckCircle, Home, AlertCircle, MessageSquare } from 'lucide-react';

import { checkTwinEligibility } from '@/lib/interviewApi';
import { generateTwin } from '@/lib/twinApi';
import type { TwinEligibilityResponse } from '@/types/interview';
import type { TwinProfile } from '@/types/twin';

function TwinGenerateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = searchParams.get('userId');

  const [status, setStatus] = useState<'checking' | 'eligible' | 'generating' | 'complete' | 'not_eligible' | 'error'>('checking');
  const [eligibility, setEligibility] = useState<TwinEligibilityResponse | null>(null);
  const [twin, setTwin] = useState<TwinProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkEligibility = useCallback(async () => {
    if (!userId) {
      setStatus('error');
      setError('No user ID provided');
      return;
    }

    try {
      const response = await checkTwinEligibility(userId);
      setEligibility(response);
      if (response.can_generate_twin) {
        setStatus('eligible');
      } else {
        setStatus('not_eligible');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check eligibility');
      setStatus('error');
    }
  }, [userId]);

  useEffect(() => {
    checkEligibility();
  }, [checkEligibility]);

  const handleGenerate = async () => {
    if (!userId || !eligibility) return;

    setStatus('generating');
    setError(null);

    try {
      const result = await generateTwin(userId, {
        trigger: 'mandatory_modules_complete',
        modules_to_include: eligibility.completed_modules,
      });

      setTwin(result);
      localStorage.setItem('darpan_twin_id', result.id);
      setStatus('complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Twin generation failed');
      setStatus('error');
    }
  };

  // Checking state
  if (status === 'checking') {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
          <p className="text-white/70">Checking eligibility...</p>
        </motion.div>
      </div>
    );
  }

  // Not eligible state
  if (status === 'not_eligible' && eligibility) {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-6 max-w-md mx-4 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="w-20 h-20 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <AlertCircle className="w-10 h-10 text-yellow-400" />
          </div>
          <h2 className="text-2xl font-bold text-white">Not Ready Yet</h2>
          <p className="text-white/70">{eligibility.message}</p>

          <div className="bg-darpan-surface rounded-lg p-4 w-full">
            <p className="text-sm text-white/50 mb-2">Missing modules:</p>
            <div className="flex flex-wrap gap-2">
              {eligibility.missing_modules.map(moduleId => (
                <span
                  key={moduleId}
                  className="px-3 py-1 bg-darpan-lime/10 text-darpan-lime text-sm rounded-full"
                >
                  {moduleId}
                </span>
              ))}
            </div>
          </div>

          <button
            onClick={() => router.push('/create/modules')}
            className="flex items-center gap-2 px-6 py-3 bg-darpan-lime text-black font-semibold rounded-lg"
          >
            Complete Modules
          </button>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (status === 'error') {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-4 max-w-md mx-4 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-white">Something went wrong</h2>
          <p className="text-white/50">{error}</p>
          <button
            onClick={() => router.push('/create/modules')}
            className="px-4 py-2 bg-white/10 text-white rounded-lg"
          >
            Back to Modules
          </button>
        </motion.div>
      </div>
    );
  }

  // Eligible state
  if (status === 'eligible') {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-6 max-w-md mx-4 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <motion.div
            className="w-24 h-24 rounded-full bg-gradient-to-r from-darpan-lime/30 to-darpan-cyan/30 flex items-center justify-center"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Sparkles className="w-12 h-12 text-darpan-lime" />
          </motion.div>

          <h2 className="text-3xl font-bold text-white">Ready to Generate!</h2>
          <p className="text-white/70">
            All 4 modules are complete. Your digital twin will be created using
            your responses to understand your preferences and decision-making style.
          </p>

          <div className="bg-darpan-surface rounded-lg p-4 w-full">
            <p className="text-sm text-white/50 mb-2">Completed modules:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {eligibility?.completed_modules.map(moduleId => (
                <span
                  key={moduleId}
                  className="flex items-center gap-1 px-3 py-1 bg-darpan-lime/10 text-darpan-lime text-sm rounded-full"
                >
                  <CheckCircle className="w-3 h-3" />
                  {moduleId}
                </span>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-darpan-lime to-darpan-cyan
                     text-black font-bold text-lg rounded-xl hover:opacity-90 transition-opacity"
          >
            <Sparkles className="w-6 h-6" />
            Generate My Digital Twin
          </button>
        </motion.div>
      </div>
    );
  }

  // Generating state
  if (status === 'generating') {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-6 max-w-md mx-4 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <motion.div
            className="w-24 h-24 rounded-full bg-gradient-to-r from-darpan-lime/30 to-darpan-cyan/30 flex items-center justify-center"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          >
            <Sparkles className="w-12 h-12 text-darpan-lime" />
          </motion.div>

          <h2 className="text-2xl font-bold text-white">Creating Your Twin...</h2>
          <p className="text-white/70">
            Analyzing your responses and building your digital personality model.
            This may take 15-30 seconds.
          </p>

          <div className="w-full bg-darpan-surface rounded-full h-2 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-darpan-lime to-darpan-cyan"
              initial={{ width: '5%' }}
              animate={{ width: '90%' }}
              transition={{ duration: 25, ease: 'easeOut' }}
            />
          </div>

          <div className="space-y-1 text-xs text-white/40">
            <p>Extracting personality profile...</p>
            <p>Building persona summary...</p>
            <p>Indexing evidence snippets...</p>
          </div>
        </motion.div>
      </div>
    );
  }

  // Complete state
  return (
    <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
      <motion.div
        className="flex flex-col items-center gap-6 max-w-md mx-4 text-center"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <motion.div
          className="w-24 h-24 rounded-full bg-darpan-lime/20 flex items-center justify-center"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
        >
          <CheckCircle className="w-12 h-12 text-darpan-lime" />
        </motion.div>

        <h2 className="text-3xl font-bold text-white">Twin Created!</h2>
        <p className="text-white/70">
          Your digital twin is ready. You can now chat with it or run experiments.
        </p>

        {twin && (
          <div className="bg-darpan-surface rounded-lg p-4 w-full text-left">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/50">Quality</span>
              <span className="text-sm font-mono text-darpan-lime">
                {twin.quality_label.toUpperCase()} ({Math.round(twin.quality_score * 100)}%)
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-white/50">Version</span>
              <span className="text-sm font-mono text-white/70">v{twin.version}</span>
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3 w-full">
          <button
            onClick={() => router.push(`/create/twin/chat?userId=${userId}`)}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-darpan-lime text-black font-semibold rounded-lg"
          >
            <MessageSquare className="w-4 h-4" />
            Chat with Your Twin
          </button>
          <button
            onClick={() => router.push('/create/modules')}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-white/10 text-white rounded-lg"
          >
            <Home className="w-4 h-4" />
            Back to Modules
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default function TwinGeneratePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
          <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
        </div>
      }
    >
      <TwinGenerateContent />
    </Suspense>
  );
}
