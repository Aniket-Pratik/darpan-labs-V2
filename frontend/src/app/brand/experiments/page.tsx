'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  FlaskConical,
  Plus,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Users,
  ArrowRight,
  MessageSquare,
} from 'lucide-react';
import { listExperiments, listCohorts } from '@/lib/experimentApi';
import { getUserIdFromStorage } from '@/lib/interviewApi';
import type { ExperimentListItem, Cohort } from '@/types/experiment';
import { STATUS_COLORS } from '@/types/experiment';

export default function ExperimentsPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string>('');
  const [experiments, setExperiments] = useState<ExperimentListItem[]>([]);
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [isLoading, setIsLoading] = useState(true);
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

    Promise.all([
      listExperiments(uid).catch(() => []),
      listCohorts(uid).catch(() => []),
    ]).then(([exps, cohs]) => {
      setExperiments(exps);
      setCohorts(cohs);
      setIsLoading(false);
    });
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
      </div>
    );
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-white/40" />;
    }
  };

  return (
    <div>
      <main className="max-w-5xl mx-auto px-4 py-12">
        {/* Title + create button */}
        <motion.div
          className="flex items-center justify-between mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div>
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <FlaskConical className="w-8 h-8 text-darpan-lime" />
              Experiments
            </h2>
            <p className="text-white/50 mt-1">
              Run scenarios against cohorts of digital twins
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/brand/chat')}
              className="flex items-center gap-2 px-5 py-2.5 border border-darpan-cyan/30
                       text-darpan-cyan rounded-lg hover:bg-darpan-cyan/10 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Chat with Twins
            </button>
            <button
              onClick={() => router.push('/brand/experiments/new')}
              className="flex items-center gap-2 px-5 py-2.5 bg-darpan-lime text-black font-semibold rounded-lg
                       hover:opacity-90 transition-opacity"
            >
              <Plus className="w-4 h-4" />
              New Experiment
            </button>
          </div>
        </motion.div>

        {/* Cohorts summary */}
        {cohorts.length > 0 && (
          <motion.section
            className="mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="flex items-center gap-2 text-white/70 font-medium mb-3">
              <Users className="w-4 h-4" />
              Your Cohorts ({cohorts.length})
            </h3>
            <div className="grid md:grid-cols-3 gap-3">
              {cohorts.slice(0, 6).map((cohort) => (
                <div
                  key={cohort.id}
                  className="p-3 bg-darpan-surface border border-darpan-border rounded-lg"
                >
                  <p className="text-sm font-medium text-white">{cohort.name}</p>
                  <p className="text-xs text-white/40 mt-1">
                    {cohort.twin_ids.length} twins
                  </p>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Experiments list */}
        {experiments.length === 0 ? (
          <motion.div
            className="text-center py-16"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <FlaskConical className="w-16 h-16 text-white/10 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white/70 mb-2">
              No experiments yet
            </h3>
            <p className="text-white/40 mb-6 max-w-md mx-auto">
              Create your first experiment to test scenarios against your digital twin cohorts.
            </p>
            <button
              onClick={() => router.push('/brand/experiments/new')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-darpan-lime text-black font-semibold rounded-lg"
            >
              <Plus className="w-4 h-4" />
              Create Experiment
            </button>
          </motion.div>
        ) : (
          <motion.div
            className="space-y-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            {experiments.map((exp) => {
              const colors = STATUS_COLORS[exp.status] || STATUS_COLORS.pending;
              return (
                <button
                  key={exp.id}
                  onClick={() => router.push(`/brand/experiments/${exp.id}`)}
                  className="w-full flex items-center justify-between p-4 bg-darpan-surface border border-darpan-border
                           rounded-lg hover:border-white/20 transition-colors text-left"
                >
                  <div className="flex items-center gap-4">
                    {statusIcon(exp.status)}
                    <div>
                      <p className="text-white font-medium">{exp.name}</p>
                      <div className="flex gap-3 text-xs text-white/40 mt-1">
                        <span>{exp.cohort_size} twins</span>
                        <span>
                          {new Date(exp.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-1 text-xs rounded ${colors.bg} ${colors.text} capitalize`}
                    >
                      {exp.status}
                    </span>
                    <ArrowRight className="w-4 h-4 text-white/20" />
                  </div>
                </button>
              );
            })}
          </motion.div>
        )}
      </main>
    </div>
  );
}
