'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, FileText } from 'lucide-react';
import type { EvidenceUsed } from '@/types/twin';

interface EvidenceDrawerProps {
  evidence: EvidenceUsed[];
}

export default function EvidenceDrawer({ evidence }: EvidenceDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white/60 transition-colors"
      >
        <FileText className="w-3 h-3" />
        <span>Evidence ({evidence.length} snippet{evidence.length !== 1 ? 's' : ''})</span>
        <ChevronDown
          className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-2">
              {evidence.map((e, i) => (
                <div
                  key={e.snippet_id || i}
                  className="bg-darpan-bg rounded-lg p-3 border border-darpan-border"
                >
                  {e.snippet_text && (
                    <p className="text-xs text-white/70 mb-1.5 italic">
                      &ldquo;{e.snippet_text}&rdquo;
                    </p>
                  )}
                  <p className="text-xs text-white/40">
                    {e.why}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
