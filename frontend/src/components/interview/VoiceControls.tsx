'use client';

import { motion } from 'framer-motion';
import { Mic, MicOff, Loader2, Keyboard } from 'lucide-react';

interface VoiceControlsProps {
  isRecording: boolean;
  isProcessing: boolean;
  isConnected: boolean;
  error: string | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onSwitchToText: () => void;
}

export function VoiceControls({
  isRecording,
  isProcessing,
  isConnected,
  error,
  onStartRecording,
  onStopRecording,
  onSwitchToText,
}: VoiceControlsProps) {
  const handleMicClick = () => {
    if (isProcessing) return;
    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Mic button */}
      <div className="relative">
        {/* Pulsing ring when recording */}
        {isRecording && (
          <motion.div
            className="absolute inset-0 rounded-full bg-red-500/20"
            animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}

        <motion.button
          type="button"
          onClick={handleMicClick}
          disabled={isProcessing}
          className={`
            relative z-10 w-16 h-16 rounded-full flex items-center justify-center
            transition-all duration-200
            ${
              isProcessing
                ? 'bg-white/10 cursor-not-allowed'
                : isRecording
                  ? 'bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30'
                  : 'bg-darpan-lime hover:bg-darpan-lime-dim shadow-lg shadow-darpan-lime/20'
            }
          `}
          whileTap={!isProcessing ? { scale: 0.95 } : undefined}
        >
          {isProcessing ? (
            <Loader2 className="w-7 h-7 text-white/50 animate-spin" />
          ) : isRecording ? (
            <MicOff className="w-7 h-7 text-white" />
          ) : (
            <Mic className="w-7 h-7 text-black" />
          )}
        </motion.button>
      </div>

      {/* Status text */}
      <p className="text-sm text-white/50">
        {isProcessing
          ? 'Processing your answer...'
          : isRecording
            ? 'Listening... tap to stop'
            : error
              ? ''
              : 'Tap to speak'}
      </p>

      {/* Error message */}
      {error && (
        <motion.p
          className="text-sm text-darpan-error text-center max-w-xs"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {error}
        </motion.p>
      )}

      {/* Switch to text */}
      <button
        type="button"
        onClick={onSwitchToText}
        className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/60 transition-colors"
      >
        <Keyboard className="w-3.5 h-3.5" />
        Switch to typing
      </button>
    </div>
  );
}
