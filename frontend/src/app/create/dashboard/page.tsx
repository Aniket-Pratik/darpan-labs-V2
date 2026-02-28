'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  User,
  MessageSquare,
  Sparkles,
  ArrowRight,
  Loader2,
  Brain,
} from 'lucide-react';
import { getUserIdFromStorage, getUserModules } from '@/lib/interviewApi';
import { getUserTwin } from '@/lib/twinApi';
import type { UserModulesResponse } from '@/types/interview';
import type { TwinProfile } from '@/types/twin';
import { QUALITY_LABELS } from '@/types/twin';

export default function DashboardPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string>('');
  const [modules, setModules] = useState<UserModulesResponse | null>(null);
  const [twin, setTwin] = useState<TwinProfile | null>(null);
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
      getUserModules(uid).catch(() => null),
      getUserTwin(uid).catch(() => null),
    ]).then(([mods, tw]) => {
      setModules(mods);
      setTwin(tw);
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

  const completedModules = modules?.completed_count || 0;
  const totalModules = modules?.total_required || 4;
  const qualityInfo = twin ? QUALITY_LABELS[twin.quality_label] : null;

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      {/* Welcome */}
      <motion.div
        className="mb-10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-3xl font-bold text-white mb-2">
          Welcome back
        </h2>
        <p className="text-white/50">
          Here&apos;s an overview of your digital twin progress.
        </p>
      </motion.div>

      {/* Quick stats */}
      <motion.div
        className="grid md:grid-cols-3 gap-4 mb-10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <StatCard
          icon={<Brain className="w-5 h-5 text-darpan-lime" />}
          label="Modules"
          value={`${completedModules}/${totalModules}`}
          sub="completed"
        />
        <StatCard
          icon={<Sparkles className="w-5 h-5 text-darpan-cyan" />}
          label="Twin"
          value={twin ? `v${twin.version}` : 'None'}
          sub={twin ? qualityInfo?.name || twin.quality_label : 'Not generated'}
        />
        <StatCard
          icon={<User className="w-5 h-5 text-white/50" />}
          label="Quality"
          value={twin ? `${Math.round(twin.quality_score * 100)}%` : '-'}
          sub={twin ? qualityInfo?.description || '' : 'No twin yet'}
        />
      </motion.div>

      {/* Quick actions */}
      <motion.div
        className="grid md:grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        {/* Modules */}
        <ActionCard
          icon={<Brain className="w-8 h-8 text-darpan-lime" />}
          title="Interview Modules"
          description={
            completedModules < totalModules
              ? `Complete ${totalModules - completedModules} more modules`
              : 'All modules complete!'
          }
          buttonLabel={completedModules < totalModules ? 'Continue' : 'Review'}
          onClick={() => router.push('/create/modules')}
        />

        {/* Chat */}
        <ActionCard
          icon={<MessageSquare className="w-8 h-8 text-darpan-cyan" />}
          title="Chat with Twin"
          description={
            twin
              ? 'Ask questions and see evidence-based answers'
              : 'Generate your twin first'
          }
          buttonLabel={twin ? 'Start Chat' : 'Generate Twin'}
          onClick={() =>
            twin
              ? router.push('/create/twin/chat')
              : router.push(`/create/twin/generate?userId=${userId}`)
          }
          disabled={!twin && completedModules < totalModules}
        />
      </motion.div>

      {/* Brand side link */}
      <motion.div
        className="mt-10 p-4 bg-darpan-surface border border-darpan-border rounded-lg text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <p className="text-white/40 text-sm">
          Want to run experiments on digital twins?{' '}
          <button
            onClick={() => router.push('/brand/experiments')}
            className="text-darpan-cyan hover:text-darpan-cyan/80 transition-colors"
          >
            Switch to Brand side &rarr;
          </button>
        </p>
      </motion.div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="p-4 bg-darpan-surface border border-darpan-border rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-white/40">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-white/30 mt-1">{sub}</p>
    </div>
  );
}

function ActionCard({
  icon,
  title,
  description,
  buttonLabel,
  onClick,
  disabled,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  buttonLabel: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="p-6 bg-darpan-surface border border-darpan-border rounded-xl flex flex-col">
      <div className="mb-4">{icon}</div>
      <h3 className="text-white font-semibold mb-1">{title}</h3>
      <p className="text-sm text-white/40 mb-4 flex-1">{description}</p>
      <button
        onClick={onClick}
        disabled={disabled}
        className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white/10 hover:bg-white/15
                 text-white text-sm font-medium rounded-lg transition-colors
                 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        {buttonLabel}
        <ArrowRight className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
