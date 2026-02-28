'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  User,
  Brain,
  Heart,
  MessageCircle,
  Check,
  Play,
  Clock,
  Sparkles,
  Loader2,
  ArrowRight,
  Coffee,
  Wallet,
  TrendingUp,
  BookOpen,
} from 'lucide-react';

import {
  getUserModules,
  getUserIdFromStorage,
  saveUserIdToStorage,
} from '@/lib/interviewApi';
import type { UserModulesResponse, UserModuleStatus } from '@/types/interview';

const moduleIcons: Record<string, React.ReactNode> = {
  M1: <User className="w-6 h-6" />,
  M2: <Brain className="w-6 h-6" />,
  M3: <Heart className="w-6 h-6" />,
  M4: <MessageCircle className="w-6 h-6" />,
  A1: <Coffee className="w-6 h-6" />,
  A2: <Wallet className="w-6 h-6" />,
  A3: <TrendingUp className="w-6 h-6" />,
  A4: <BookOpen className="w-6 h-6" />,
};

const moduleColors: Record<string, string> = {
  M1: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
  M2: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
  M3: 'from-pink-500/20 to-pink-600/10 border-pink-500/30',
  M4: 'from-green-500/20 to-green-600/10 border-green-500/30',
  A1: 'from-amber-500/20 to-amber-600/10 border-amber-500/30',
  A2: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30',
  A3: 'from-sky-500/20 to-sky-600/10 border-sky-500/30',
  A4: 'from-indigo-500/20 to-indigo-600/10 border-indigo-500/30',
};

const moduleIconColors: Record<string, string> = {
  M1: 'text-blue-400',
  M2: 'text-purple-400',
  M3: 'text-pink-400',
  M4: 'text-green-400',
  A1: 'text-amber-400',
  A2: 'text-emerald-400',
  A3: 'text-sky-400',
  A4: 'text-indigo-400',
};

const DEFAULT_MODULES: UserModuleStatus[] = [
  { module_id: 'M1', module_name: 'Core Identity & Context', description: 'Understanding who you are and your life context', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'M2', module_name: 'Decision Logic & Risk', description: 'How you make decisions and handle uncertainty', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'M3', module_name: 'Preferences & Values', description: 'Your priorities and what matters to you', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'M4', module_name: 'Communication & Social', description: 'Your interaction style and social tendencies', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'A1', module_name: 'Lifestyle & Routines', description: 'Your daily habits, routines, and lifestyle choices', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'A2', module_name: 'Spending & Financial Behavior', description: 'How you manage money and make purchase decisions', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'A3', module_name: 'Career & Growth Aspirations', description: 'Your career goals and personal growth mindset', status: 'not_started', estimated_duration_min: 3 },
  { module_id: 'A4', module_name: 'Work & Learning Style', description: 'How you work, learn, and solve problems', status: 'not_started', estimated_duration_min: 3 },
];

export default function ModulesPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [userId, setUserId] = useState<string>('');
  const [modulesData, setModulesData] = useState<UserModulesResponse | null>(null);
  const hasFetched = useRef(false);

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    let uid = getUserIdFromStorage();
    if (!uid) {
      uid = crypto.randomUUID();
      saveUserIdToStorage(uid);
    }
    setUserId(uid);

    getUserModules(uid)
      .then((data) => {
        setModulesData(data);
      })
      .catch((err) => {
        console.error('Failed to fetch modules:', err);
        setModulesData({
          user_id: uid,
          modules: DEFAULT_MODULES,
          completed_count: 0,
          total_required: 4,
          can_generate_twin: false,
        });
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const handleStartModule = (moduleId: string) => {
    router.push(`/create/modules/${moduleId}/start?userId=${userId}`);
  };

  const handleGenerateTwin = () => {
    router.push(`/create/twin/generate?userId=${userId}`);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
          <p className="text-white/70">Loading your progress...</p>
        </div>
      </div>
    );
  }

  const modules = modulesData?.modules ?? DEFAULT_MODULES;
  const completedCount = modulesData?.completed_count ?? 0;
  const totalRequired = modulesData?.total_required ?? 4;
  const canGenerateTwin = modulesData?.can_generate_twin ?? false;

  const mandatoryModules = modules.filter((m) => m.module_id.startsWith('M'));
  const addonModules = modules.filter((m) => m.module_id.startsWith('A'));

  return (
    <div>
      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        {/* Progress header */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-3xl font-bold text-white mb-4">
            Build Your Digital Twin
          </h2>
          <p className="text-white/60 mb-6">
            Complete all 4 core modules to create your AI twin. Add-on modules enhance your twin further.
          </p>

          {/* Progress bar */}
          <div className="max-w-md mx-auto">
            <div className="flex items-center justify-between text-sm text-white/50 mb-2">
              <span>Core Progress</span>
              <span>{completedCount} of {totalRequired} modules</span>
            </div>
            <div className="h-2 bg-darpan-surface rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-darpan-lime to-darpan-cyan"
                initial={{ width: 0 }}
                animate={{ width: `${(completedCount / totalRequired) * 100}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        </motion.div>

        {/* Core modules section */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-white mb-1">Core Modules</h3>
          <p className="text-sm text-white/40 mb-4">Required to generate your digital twin</p>
        </div>
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {mandatoryModules.map((module, index) => (
            <ModuleCard
              key={module.module_id}
              module={module}
              index={index}
              onStart={() => handleStartModule(module.module_id)}
            />
          ))}
        </div>

        {/* Add-on modules section */}
        {addonModules.length > 0 && (
          <>
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-white mb-1">Add-on Modules</h3>
              <p className="text-sm text-white/40 mb-4">Optional — enhance your twin with deeper insights</p>
            </div>
            <div className="grid md:grid-cols-2 gap-6 mb-12">
              {addonModules.map((module, index) => (
                <ModuleCard
                  key={module.module_id}
                  module={module}
                  index={index + mandatoryModules.length}
                  onStart={() => handleStartModule(module.module_id)}
                />
              ))}
            </div>
          </>
        )}

        {/* Generate Twin button */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          {canGenerateTwin ? (
            <button
              onClick={handleGenerateTwin}
              className="flex items-center gap-3 px-8 py-4 mx-auto bg-gradient-to-r from-darpan-lime to-darpan-cyan
                       text-black font-bold text-lg rounded-xl hover:opacity-90
                       transition-opacity shadow-glow-lime"
            >
              <Sparkles className="w-6 h-6" />
              Generate Your Digital Twin
              <ArrowRight className="w-5 h-5" />
            </button>
          ) : (
            <div className="bg-darpan-surface border border-darpan-border rounded-xl p-6 max-w-md mx-auto">
              <Sparkles className="w-8 h-8 text-white/30 mx-auto mb-3" />
              <p className="text-white/50 text-sm">
                Complete all {totalRequired} modules to unlock your digital twin
              </p>
            </div>
          )}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-darpan-border mt-16">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center">
          <p className="text-xs text-white/30">
            Your responses are private and used only to create your digital twin.
          </p>
        </div>
      </footer>
    </div>
  );
}

function ModuleCard({
  module,
  index,
  onStart,
}: {
  module: UserModuleStatus;
  index: number;
  onStart: () => void;
}) {
  const isCompleted = module.status === 'completed';
  const isInProgress = module.status === 'in_progress';

  return (
    <motion.div
      className={`relative bg-gradient-to-br ${moduleColors[module.module_id]}
                  border rounded-xl p-6 ${isCompleted ? 'opacity-80' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      {/* Completed badge */}
      {isCompleted && (
        <div className="absolute top-4 right-4">
          <div className="flex items-center gap-1 px-2 py-1 bg-darpan-lime/20 rounded-full">
            <Check className="w-4 h-4 text-darpan-lime" />
            <span className="text-xs font-medium text-darpan-lime">Complete</span>
          </div>
        </div>
      )}

      {/* In progress badge */}
      {isInProgress && (
        <div className="absolute top-4 right-4">
          <div className="flex items-center gap-1 px-2 py-1 bg-darpan-cyan/20 rounded-full">
            <Clock className="w-4 h-4 text-darpan-cyan" />
            <span className="text-xs font-medium text-darpan-cyan">In Progress</span>
          </div>
        </div>
      )}

      {/* Module icon */}
      <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-4 ${moduleIconColors[module.module_id]}`}>
        {moduleIcons[module.module_id]}
      </div>

      {/* Module info */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono text-white/40">{module.module_id}</span>
          <span className="text-xs text-white/30">~{module.estimated_duration_min} min</span>
        </div>
        <h3 className="text-lg font-semibold text-white mb-1">{module.module_name}</h3>
        <p className="text-sm text-white/50">{module.description}</p>
      </div>

      {/* Completion scores */}
      {isCompleted && module.coverage_score != null && (
        <div className="flex gap-4 mb-4 text-xs">
          <div>
            <span className="text-white/40">Coverage:</span>
            <span className="ml-1 text-darpan-lime font-medium">
              {Math.round(module.coverage_score * 100)}%
            </span>
          </div>
          <div>
            <span className="text-white/40">Confidence:</span>
            <span className="ml-1 text-darpan-cyan font-medium">
              {Math.round((module.confidence_score ?? 0) * 100)}%
            </span>
          </div>
        </div>
      )}

      {/* Action button */}
      {!isCompleted && (
        <button
          onClick={onStart}
          className="w-full flex items-center justify-center gap-2 px-4 py-3
                   bg-white/10 hover:bg-white/15 text-white font-medium
                   rounded-lg transition-colors"
        >
          <Play className="w-4 h-4" />
          {isInProgress ? 'Continue' : 'Start Module'}
        </button>
      )}
    </motion.div>
  );
}
