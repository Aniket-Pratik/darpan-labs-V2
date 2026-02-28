'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { MessageSquare, Loader2, Clock } from 'lucide-react';
import { BrandChatContainer, TwinSelector } from '@/components/twin';
import { listBrandChatSessions } from '@/lib/twinApi';
import { getUserIdFromStorage } from '@/lib/interviewApi';
import type { BrandChatSessionItem } from '@/types/twin';
import { QUALITY_LABELS } from '@/types/twin';

function BrandChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const twinIdParam = searchParams.get('twinId');

  const [userId, setUserId] = useState<string>('');
  const [step, setStep] = useState<'select' | 'chat'>(twinIdParam ? 'chat' : 'select');
  const [selectedTwinId, setSelectedTwinId] = useState<string | null>(twinIdParam);
  const [sessions, setSessions] = useState<BrandChatSessionItem[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
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

    listBrandChatSessions(uid)
      .then(setSessions)
      .catch(() => {})
      .finally(() => setIsLoadingSessions(false));
  }, [router]);

  const handleSelectTwin = (twinId: string) => {
    setSelectedTwinId(twinId);
    setStep('chat');
  };

  const handleBack = () => {
    setStep('select');
    setSelectedTwinId(null);
    if (userId) {
      listBrandChatSessions(userId)
        .then(setSessions)
        .catch(() => {});
    }
  };

  if (!userId) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
      </div>
    );
  }

  if (step === 'chat' && selectedTwinId) {
    return <BrandChatContainer userId={userId} twinId={selectedTwinId} onBack={handleBack} />;
  }

  return (
    <div>
      <main className="max-w-5xl mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-darpan-lime" />
            Chat with Twins
          </h2>
          <p className="text-white/50 mt-1">
            Have free-form conversations with individual digital twins
          </p>
        </motion.div>

        {/* Past sessions */}
        {!isLoadingSessions && sessions.length > 0 && (
          <motion.section
            className="mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="flex items-center gap-2 text-white/70 font-medium mb-3">
              <Clock className="w-4 h-4" />
              Recent Conversations ({sessions.length})
            </h3>
            <div className="grid md:grid-cols-3 gap-3">
              {sessions.slice(0, 6).map((session) => {
                const qualityInfo = QUALITY_LABELS[session.twin_quality_label];
                return (
                  <button
                    key={session.id}
                    onClick={() => handleSelectTwin(session.twin_id)}
                    className="p-3 bg-darpan-surface border border-darpan-border rounded-lg
                             hover:border-darpan-lime/50 transition-colors text-left"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono text-white/40">
                        {session.twin_id.slice(0, 8)}
                      </span>
                      <span
                        className="text-xs font-medium"
                        style={{ color: qualityInfo?.color || '#fff' }}
                      >
                        {qualityInfo?.name || session.twin_quality_label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-white/40">
                      <span>{session.message_count} messages</span>
                      <span>{new Date(session.created_at).toLocaleDateString()}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </motion.section>
        )}

        {/* Twin selector */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-white/70 font-medium mb-4">Select a Twin</h3>
          <TwinSelector
            userId={userId}
            onSelectTwin={handleSelectTwin}
            existingSessions={sessions}
          />
        </motion.section>
      </main>
    </div>
  );
}

export default function BrandChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center py-24">
          <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
        </div>
      }
    >
      <BrandChatContent />
    </Suspense>
  );
}
