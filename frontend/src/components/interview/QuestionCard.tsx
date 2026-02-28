'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, SkipForward, Loader2, Mic, Square } from 'lucide-react';
import type { Question } from '@/store/interviewStore';

interface QuestionCardProps {
  question: Question;
  answer: string;
  onAnswerChange: (answer: string) => void;
  onSubmit: () => void;
  onSkip: (reason?: string) => void;
  isSubmitting: boolean;
  moduleName?: string;
  acknowledgmentText?: string | null;
  // Voice props
  isRecording?: boolean;
  isProcessingVoice?: boolean;
  voiceError?: string | null;
  finalTranscript?: string;
  timeoutMessage?: string | null;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
}

/** Animated waveform bars shown inside the textarea while recording. */
function WaveformAnimation() {
  const bars = 5;
  return (
    <div className="flex items-center justify-center gap-1 h-full">
      {Array.from({ length: bars }).map((_, i) => (
        <motion.div
          key={i}
          className="w-1 rounded-full bg-darpan-lime"
          animate={{
            height: ['12px', '28px', '12px'],
          }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.12,
            ease: 'easeInOut',
          }}
        />
      ))}
      <span className="ml-3 text-sm text-white/40">Recording...</span>
    </div>
  );
}

export function QuestionCard({
  question,
  answer,
  onAnswerChange,
  onSubmit,
  onSkip,
  isSubmitting,
  moduleName,
  acknowledgmentText = null,
  isRecording = false,
  isProcessingVoice = false,
  voiceError = null,
  finalTranscript = '',
  timeoutMessage = null,
  onStartRecording,
  onStopRecording,
}: QuestionCardProps) {
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  // When a voice transcript arrives, fill the textarea
  useEffect(() => {
    if (finalTranscript) {
      onAnswerChange(finalTranscript);
    }
  }, [finalTranscript, onAnswerChange]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim() && !isSubmitting && !isRecording) {
      onSubmit();
    }
  };

  const handleSkip = () => {
    if (showSkipConfirm) {
      onSkip('User chose to skip');
      setShowSkipConfirm(false);
    } else {
      setShowSkipConfirm(true);
    }
  };

  const handleMicClick = () => {
    if (isProcessingVoice || isSubmitting) return;
    if (isRecording) {
      onStopRecording?.();
    } else {
      onStartRecording?.();
    }
  };

  const isBusy = isSubmitting || isProcessingVoice;

  return (
    <motion.div
      className="w-full max-w-2xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      {/* Module badge */}
      {moduleName && (
        <div className="mb-4">
          <span className="inline-block px-3 py-1 text-xs font-medium rounded-full bg-darpan-lime/10 text-darpan-lime border border-darpan-lime/20">
            {moduleName}
          </span>
        </div>
      )}

      {/* Question card */}
      <div className="bg-darpan-surface border border-darpan-border rounded-xl p-6 shadow-lg">
        {/* Acknowledgment text */}
        <AnimatePresence>
          {acknowledgmentText && (
            <motion.p
              className="text-sm italic text-white/60 mb-4 leading-relaxed"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {acknowledgmentText}
            </motion.p>
          )}
        </AnimatePresence>

        {/* Question text */}
        <motion.h2
          className="text-xl font-medium text-white mb-6 leading-relaxed"
          key={question.question_id}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: acknowledgmentText ? 0.2 : 0.1 }}
        >
          {question.question_text}
        </motion.h2>

        {/* Unified input area */}
        <form onSubmit={handleSubmit}>
          <div className="relative">
            {/* Recording waveform overlay */}
            <AnimatePresence>
              {isRecording && (
                <motion.div
                  className="absolute inset-0 z-10 bg-darpan-bg/90 border border-darpan-lime/30 rounded-lg
                             flex items-center justify-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <WaveformAnimation />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Textarea — always visible, user can type or see transcript */}
            <textarea
              value={answer}
              onChange={(e) => onAnswerChange(e.target.value)}
              placeholder="Type or tap the mic to speak..."
              className="w-full h-32 px-4 py-3 pr-14 bg-darpan-bg border border-darpan-border rounded-lg
                         text-white placeholder-white/30 resize-none
                         focus:outline-none focus:border-darpan-lime/50 focus:ring-1 focus:ring-darpan-lime/30
                         transition-colors duration-200"
              disabled={isBusy || isRecording}
              autoFocus
            />

            {/* Mic button — inside textarea, bottom-right */}
            <button
              type="button"
              onClick={handleMicClick}
              disabled={isBusy}
              className={`
                absolute bottom-3 right-3 z-20 w-9 h-9 rounded-full
                flex items-center justify-center transition-all duration-200
                ${
                  isBusy
                    ? 'bg-white/5 cursor-not-allowed'
                    : isRecording
                      ? 'bg-red-500 hover:bg-red-600 shadow-md shadow-red-500/30'
                      : 'bg-white/10 hover:bg-white/20'
                }
              `}
            >
              {isBusy ? (
                <Loader2 className="w-4 h-4 text-white/30 animate-spin" />
              ) : isRecording ? (
                <Square className="w-3.5 h-3.5 text-white fill-white" />
              ) : (
                <Mic className="w-4 h-4 text-white/60" />
              )}
            </button>
          </div>

          {/* Voice error */}
          <AnimatePresence>
            {voiceError && (
              <motion.p
                className="mt-2 text-xs text-red-400"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {voiceError}
              </motion.p>
            )}
          </AnimatePresence>

          {/* Timeout prompt */}
          <AnimatePresence>
            {timeoutMessage && (
              <motion.p
                className="mt-2 text-sm text-darpan-lime/70 italic"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {timeoutMessage}
              </motion.p>
            )}
          </AnimatePresence>

          {/* Action buttons */}
          <div className="flex items-center justify-between mt-4">
            {/* Left: Skip */}
            <div className="relative">
              {showSkipConfirm ? (
                <motion.div
                  className="flex items-center gap-2"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                >
                  <span className="text-sm text-white/50">Skip this question?</span>
                  <button
                    type="button"
                    onClick={handleSkip}
                    className="px-3 py-1.5 text-sm text-darpan-warning hover:text-darpan-warning/80 transition-colors"
                    disabled={isBusy}
                  >
                    Yes, skip
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowSkipConfirm(false)}
                    className="px-3 py-1.5 text-sm text-white/50 hover:text-white/70 transition-colors"
                    disabled={isBusy}
                  >
                    Cancel
                  </button>
                </motion.div>
              ) : (
                <button
                  type="button"
                  onClick={handleSkip}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-white/50
                           hover:text-white/70 transition-colors"
                  disabled={isBusy}
                >
                  <SkipForward className="w-4 h-4" />
                  Skip
                </button>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isBusy || isRecording || !answer.trim()}
              className="flex items-center gap-2 px-6 py-2.5
                       bg-darpan-lime text-black font-semibold rounded-lg
                       hover:bg-darpan-lime-dim transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isBusy ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Submit
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Question meta (optional, for debug) */}
      {question.target_signal && process.env.NODE_ENV === 'development' && (
        <p className="mt-2 text-xs text-white/20 text-center">
          Signal: {question.target_signal}
        </p>
      )}
    </motion.div>
  );
}
