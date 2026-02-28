'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Loader2, AlertCircle, MessageSquare } from 'lucide-react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import TwinProfileCard from './TwinProfileCard';
import { sendChatMessage, getUserTwin } from '@/lib/twinApi';
import type { TwinProfile, ChatMessage as ChatMessageType, TwinChatResponse } from '@/types/twin';

interface ChatContainerProps {
  userId: string;
  twinId?: string;
}

export default function ChatContainer({ userId, twinId }: ChatContainerProps) {
  const [twin, setTwin] = useState<TwinProfile | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTwinLoading, setIsTwinLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSuggestedModule, setLastSuggestedModule] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load twin profile
  useEffect(() => {
    async function loadTwin() {
      try {
        setIsTwinLoading(true);
        const profile = await getUserTwin(userId);
        if (profile) {
          setTwin(profile);
        } else {
          setError('No twin found. Please generate your twin first.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load twin');
      } finally {
        setIsTwinLoading(false);
      }
    }
    loadTwin();
  }, [userId, twinId]);

  const handleSend = async (message: string) => {
    if (!twin) return;

    // Add user message optimistically
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

      // Update session ID
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      // Add twin response
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
      // Remove the optimistic user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  // Loading twin
  if (isTwinLoading) {
    return (
      <div className="min-h-screen bg-darpan-bg flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-darpan-lime animate-spin" />
      </div>
    );
  }

  // Error / no twin
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
        </motion.div>
      </div>
    );
  }

  if (!twin) return null;

  return (
    <div className="min-h-screen bg-darpan-bg flex flex-col">
      {/* Twin profile header */}
      <TwinProfileCard twin={twin} compact />

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {/* Empty state */}
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
                Chat with your twin
              </h3>
              <p className="text-sm text-white/30 max-w-sm">
                Ask questions about preferences, decisions, or how your twin would react
                to different scenarios.
              </p>
            </motion.div>
          )}

          {/* Messages */}
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

          {/* Error inline */}
          {error && messages.length > 0 && (
            <div className="flex items-center gap-2 justify-center text-xs text-darpan-error">
              <AlertCircle className="w-3 h-3" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}
