'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, Check, Filter, Loader2 } from 'lucide-react';
import { getAvailableTwins, createCohort } from '@/lib/experimentApi';
import type { TwinSummary, CohortCreateResponse } from '@/types/experiment';
import { QUALITY_LABELS } from '@/types/twin';

interface CohortBuilderProps {
  userId: string;
  onCohortCreated: (cohort: CohortCreateResponse) => void;
}

export function CohortBuilder({ userId, onCohortCreated }: CohortBuilderProps) {
  const [twins, setTwins] = useState<TwinSummary[]>([]);
  const [selectedTwins, setSelectedTwins] = useState<Set<string>>(new Set());
  const [cohortName, setCohortName] = useState('');
  const [minQuality, setMinQuality] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    loadTwins();
  }, [userId, minQuality]);

  const loadTwins = async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      const result = await getAvailableTwins(userId, minQuality || undefined);
      setTwins(result);
    } catch (err) {
      setError('Failed to load available twins');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTwin = (twinId: string) => {
    setSelectedTwins((prev) => {
      const next = new Set(prev);
      if (next.has(twinId)) {
        next.delete(twinId);
      } else if (next.size < 50) {
        next.add(twinId);
      }
      return next;
    });
  };

  const selectAll = () => {
    if (selectedTwins.size === twins.length) {
      setSelectedTwins(new Set());
    } else {
      setSelectedTwins(new Set(twins.slice(0, 50).map((t) => t.twin_id)));
    }
  };

  const handleCreate = async () => {
    if (!cohortName.trim() || selectedTwins.size === 0) return;

    setIsCreating(true);
    setError(null);
    try {
      const result = await createCohort(userId, {
        name: cohortName.trim(),
        twin_ids: Array.from(selectedTwins),
        filters: minQuality ? { min_quality: minQuality as 'base' | 'enhanced' | 'rich' | 'full' } : null,
      });
      onCohortCreated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create cohort');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Cohort name */}
      <div>
        <label className="block text-sm text-white/50 mb-2">Cohort Name</label>
        <input
          type="text"
          value={cohortName}
          onChange={(e) => setCohortName(e.target.value)}
          placeholder="e.g., Urban millennials, Health-conscious users"
          className="w-full px-4 py-3 bg-darpan-surface border border-darpan-border rounded-lg
                   text-white placeholder-white/30 focus:border-darpan-lime focus:outline-none"
        />
      </div>

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

      {/* Twin selection */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-white/50">
            {selectedTwins.size} of {twins.length} twins selected
          </span>
          <button
            onClick={selectAll}
            className="text-xs text-darpan-lime hover:text-darpan-lime/80"
          >
            {selectedTwins.size === twins.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-darpan-lime animate-spin" />
          </div>
        ) : twins.length === 0 ? (
          <div className="text-center py-8 text-white/40">
            <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No twins available. Generate twins first.</p>
          </div>
        ) : (
          <div className="grid gap-2 max-h-64 overflow-y-auto pr-1">
            {twins.map((twin) => {
              const isSelected = selectedTwins.has(twin.twin_id);
              const qualityInfo = QUALITY_LABELS[twin.quality_label];
              return (
                <motion.button
                  key={twin.twin_id}
                  onClick={() => toggleTwin(twin.twin_id)}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-colors text-left ${
                    isSelected
                      ? 'border-darpan-lime/50 bg-darpan-lime/5'
                      : 'border-darpan-border bg-darpan-surface hover:border-white/20'
                  }`}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-5 h-5 rounded border flex items-center justify-center ${
                        isSelected
                          ? 'border-darpan-lime bg-darpan-lime'
                          : 'border-white/30'
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3 text-black" />}
                    </div>
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
                </motion.button>
              );
            })}
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {/* Create button */}
      <button
        onClick={handleCreate}
        disabled={!cohortName.trim() || selectedTwins.size === 0 || isCreating}
        className="w-full flex items-center justify-center gap-2 px-6 py-3
                 bg-darpan-lime text-black font-semibold rounded-lg
                 disabled:opacity-30 disabled:cursor-not-allowed
                 hover:opacity-90 transition-opacity"
      >
        {isCreating ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Users className="w-4 h-4" />
        )}
        Create Cohort ({selectedTwins.size} twins)
      </button>
    </div>
  );
}
