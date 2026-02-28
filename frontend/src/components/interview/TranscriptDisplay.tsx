'use client';

import { motion, AnimatePresence } from 'framer-motion';

interface TranscriptDisplayProps {
  isRecording: boolean;
  finalTranscript: string;
  isProcessing: boolean;
  timeoutMessage?: string | null;
}

export function TranscriptDisplay({
  isRecording,
  finalTranscript,
  isProcessing,
  timeoutMessage,
}: TranscriptDisplayProps) {
  const hasContent = isRecording || finalTranscript || isProcessing;

  if (!hasContent && !timeoutMessage) {
    return null;
  }

  return (
    <div className="w-full min-h-[80px] px-4 py-3 bg-darpan-bg border border-darpan-border rounded-lg">
      {/* Final transcript */}
      {finalTranscript && (
        <p className="leading-relaxed">
          <span className="text-white">{finalTranscript}</span>
        </p>
      )}

      {/* Listening indicator — VAD detected speech */}
      <AnimatePresence>
        {isRecording && !finalTranscript && !isProcessing && (
          <motion.p
            key="listening"
            className="text-white/40 text-sm flex items-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.span
              className="inline-block w-2 h-2 rounded-full bg-darpan-lime"
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
            Listening...
          </motion.p>
        )}
      </AnimatePresence>

      {/* Processing indicator */}
      <AnimatePresence>
        {isProcessing && !finalTranscript && (
          <motion.p
            key="processing"
            className="text-white/30 text-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            Processing your response...
          </motion.p>
        )}
      </AnimatePresence>

      {/* Timeout/silence prompt */}
      {timeoutMessage && (
        <motion.p
          className="mt-2 text-sm text-darpan-lime/70 italic"
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {timeoutMessage}
        </motion.p>
      )}
    </div>
  );
}
