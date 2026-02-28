'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, Filter, Loader2, MessageSquare } from 'lucide-react';
import { getAvailableTwins } from '@/lib/experimentApi';
import type { TwinSummary } from '@/types/experiment';
import type { BrandChatSessionItem } from '@/types/twin';
import { QUALITY_LABELS } from '@/types/twin';

interface TwinSelectorProps {
  userId: string;
  onSelectTwin: (twinId: string) => void;
  existingSessions?: BrandChatSessionItem[];
}

export default function TwinSelector({ userId, onSelectTwin, existingSessions = [] }: TwinSelectorProps) {
  const [twins, setTwins] = useState<TwinSummary[]>([]);
  const [minQuality, setMinQuality] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Build a set of twin IDs that have existing sessions + their message counts
  const sessionMap = new Map<string, number>();
  for (const s of existingSessions) {
    const existing = sessionMap.get(s.twin_id) || 0;
    sessionMap.set(s.twin_id, existing + s.message_count);
  }

  useEffect(() => {
    if (!userId) return;
    setIsLoading(true);
    getAvailableTwins(userId, minQuality || undefined)
      .then(setTwins)
      .catch(() => setError('Failed to load available twins'))
      .finally(() => setIsLoading(false));
  }, [userId, minQuality]);

  return (
    <div className="space-y-6">
      {/* Quality filter */}
      <div>
        <label className="flex items-center gap-2 text-sm text-white/50 mb-2">
          <Filter className="w-4 h-4" />
          Filter by Quality
        </label>
        <div className="flex gap-2">
          {['', 'base', 'enhanced', 'rich', 'full'].map((q) => (
            <button
              key={q || 'all'}
              onClick={() => setMinQuality(q)}
              className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                minQuality === q
                  ? 'border-darpan-lime bg-darpan-lime/10 text-darpan-lime'
                  : 'border-darpan-border text-white/50 hover:border-white/30'
              }`}
            >
              {q ? (QUALITY_LABELS[q]?.name || q) : 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Twin grid */}
      <div>
        <p className="text-sm text-white/50 mb-3">
          {twins.length} twin{twins.length !== 1 ? 's' : ''} available — click to start chatting
        </p>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-darpan-lime animate-spin" />
          </div>
        ) : error ? (
          <p className="text-sm text-red-400 text-center py-8">{error}</p>
        ) : twins.length === 0 ? (
          <div className="text-center py-8 text-white/40">
            <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No twins available. Generate twins first.</p>
          </div>
        ) : (
          <div className="grid gap-2 max-h-96 overflow-y-auto pr-1">
            {twins.map((twin) => {
              const qualityInfo = QUALITY_LABELS[twin.quality_label];
              const msgCount = sessionMap.get(twin.twin_id);
              return (
                <motion.button
                  key={twin.twin_id}
                  onClick={() => onSelectTwin(twin.twin_id)}
                  className="flex items-center justify-between p-3 rounded-lg border
                           border-darpan-border bg-darpan-surface hover:border-darpan-lime/50
                           hover:bg-darpan-lime/5 transition-colors text-left"
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-center gap-3">
                    <div>
                      <span className="text-xs font-mono text-white/40">
                        {twin.twin_id.slice(0, 8)}
                      </span>
                      <div className="flex gap-1 mt-0.5">
                        {twin.modules_completed.map((m) => (
                          <span
                            key={m}
                            className="text-[10px] px-1 py-0.5 bg-white/5 rounded text-white/40"
                          >
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {msgCount !== undefined && (
                      <span className="flex items-center gap-1 text-[10px] text-darpan-cyan/70">
                        <MessageSquare className="w-3 h-3" />
                        {msgCount}
                      </span>
                    )}
                    <div className="text-right">
                      <span
                        className="text-xs font-medium"
                        style={{ color: qualityInfo?.color || '#fff' }}
                      >
                        {qualityInfo?.name || twin.quality_label}
                      </span>
                      <p className="text-[10px] text-white/30">
                        {Math.round(twin.quality_score * 100)}%
                      </p>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
