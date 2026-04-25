import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { UnifiedDiffHeatmap } from './UnifiedDiffHeatmap';
import { CompositeRankingChart } from './CompositeRankingChart';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

export function DiagnosticSection({ data }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-darpan-surface border border-darpan-border rounded-xl overflow-hidden"
    >
      <button
        type="button"
        onClick={() => setOpen((x) => !x)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div>
          <h3 className="text-sm font-semibold text-white">Diagnostic details</h3>
          <p className="text-xs text-white/35 mt-0.5">
            Unified Δ heatmap and composite ranking — expand to stress-test the verdict
          </p>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-white/40 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-4 border-t border-darpan-border pt-4">
              <UnifiedDiffHeatmap data={data} />
              <CompositeRankingChart data={data} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
