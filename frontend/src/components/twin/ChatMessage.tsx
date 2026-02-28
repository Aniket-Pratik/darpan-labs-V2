'use client';

import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';
import EvidenceDrawer from './EvidenceDrawer';
import type { ChatMessage as ChatMessageType } from '@/types/twin';

interface ChatMessageProps {
  message: ChatMessageType;
  suggestedModule?: string;
}

export default function ChatMessage({ message, suggestedModule }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-darpan-lime/20'
            : 'bg-darpan-cyan/20'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-darpan-lime" />
        ) : (
          <Bot className="w-4 h-4 text-darpan-cyan" />
        )}
      </div>

      {/* Message bubble */}
      <div
        className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}
      >
        <div
          className={`rounded-xl px-4 py-3 ${
            isUser
              ? 'bg-darpan-elevated border border-darpan-border-active'
              : 'bg-darpan-surface border-l-2 border-darpan-cyan/40'
          }`}
        >
          <p className="text-sm text-white/90 whitespace-pre-wrap">
            {message.content}
          </p>
        </div>

        {/* Twin response metadata */}
        {!isUser && (
          <div className="mt-1.5 flex flex-col gap-1">
            <div className="flex items-center gap-2">
              {message.confidence_label && (
                <ConfidenceBadge
                  label={message.confidence_label}
                  score={message.confidence_score}
                />
              )}
              <span className="text-[10px] text-white/20 font-mono">
                {new Date(message.created_at).toLocaleTimeString()}
              </span>
            </div>

            {message.evidence_used && message.evidence_used.length > 0 && (
              <EvidenceDrawer evidence={message.evidence_used} />
            )}

            {suggestedModule && (
              <p className="text-xs text-darpan-lime/70 mt-1">
                Complete module {suggestedModule} to improve this answer
              </p>
            )}
          </div>
        )}

        {/* User message timestamp */}
        {isUser && (
          <div className="mt-1 text-right">
            <span className="text-[10px] text-white/20 font-mono">
              {new Date(message.created_at).toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
