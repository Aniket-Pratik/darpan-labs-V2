'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Loader2, AlertCircle, MessageSquare, ArrowLeft } from 'lucide-react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import TwinProfileCard from './TwinProfileCard';
import { sendChatMessage, getTwinProfile } from '@/lib/twinApi';
import type { TwinProfile, ChatMessage as ChatMessageType, TwinChatResponse } from '@/types/twin';

interface BrandChatContainerProps {
  userId: string;
  twinId: string;
  onBack?: () => void;
}

export default function BrandChatContainer({ userId, twinId, onBack }: BrandChatContainerProps) {
  const [twin, setTwin] = useState<TwinProfile | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTwinLoading, setIsTwinLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSuggestedModule, setLastSuggestedModule] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load twin profile by ID
  useEffect(() => {
    async function loadTwin() {
      try {
        setIsTwinLoading(true);
        const profile = await getTwinProfile(twinId);
        if (profile) {
          setTwin(profile);
        } else {
          setError('Twin not found.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load twin');
      } finally {
        setIsTwinLoading(false);
      }
    }
    loadTwin();
  }, [twinId]);

  const handleSend = async (message: string) => {
    if (!twin) return;

    const userMsg: ChatMessageType = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);
    setLastSuggestedModule(null);

    try {
      const response: TwinChatResponse = await sendChatMessage(
        twin.id,
        userId,
        {
          message,
          session_id: sessionId || undefined,
        }
      );

      if (!sessionId) {
        setSessionId(response.session_id);
      }

      const twinMsg: ChatMessageType = {
        id: response.message_id,
        role: 'twin',
        content: response.response_text,
        confidence_score: response.confidence_score,
        confidence_label: response.confidence_label,
        evidence_used: response.evidence_used,
        coverage_gaps: response.coverage_gaps,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, twinMsg]);
      setLastSuggestedModule(response.suggested_module || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get response');
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  if (isTwinLoading) {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-darpan-lime animate-spin" />
      </div>
    );
  }

  if (error && !twin) {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <motion.div
          className="flex flex-col items-center gap-4 text-center max-w-md mx-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <AlertCircle className="w-10 h-10 text-darpan-error" />
          <p className="text-white/70">{error}</p>
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-sm text-darpan-lime hover:text-darpan-lime/80"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to twin selector
            </button>
          )}
        </motion.div>
      </div>
    );
  }

  if (!twin) return null;

  return (
    <div className="min-h-screen bg-darpan-bg flex flex-col">
      {/* Back button + Twin profile header */}
      <div>
        {onBack && (
          <div className="px-4 py-2 bg-darpan-surface border-b border-darpan-border">
            <button
              onClick={onBack}
              className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white/80 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to twin selector
            </button>
          </div>
        )}
        <TwinProfileCard twin={twin} compact label="Digital Twin" />
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <motion.div
              className="flex flex-col items-center justify-center py-20 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="w-16 h-16 rounded-full bg-darpan-cyan/10 flex items-center justify-center mb-4">
                <MessageSquare className="w-8 h-8 text-darpan-cyan/50" />
              </div>
              <h3 className="text-lg font-medium text-white/50 mb-2">
                Chat with this twin
              </h3>
              <p className="text-sm text-white/30 max-w-sm">
                Ask this twin about their preferences, decisions, or how they&apos;d react
                to your product or scenario.
              </p>
            </motion.div>
          )}

          {messages.map((msg, i) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              suggestedModule={
                i === messages.length - 1 && msg.role === 'twin'
                  ? lastSuggestedModule || undefined
                  : undefined
              }
            />
          ))}

          {error && messages.length > 0 && (
            <div className="flex items-center gap-2 justify-center text-xs text-darpan-error">
              <AlertCircle className="w-3 h-3" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}
