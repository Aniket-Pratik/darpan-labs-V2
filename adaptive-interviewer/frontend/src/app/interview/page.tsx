"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuid } from "uuid";

import { ChatLog } from "@/components/ChatLog";
import { Composer } from "@/components/Composer";
import { ProgressBar } from "@/components/ProgressBar";
import { completeInterview, getState, postTurn, startInterview } from "@/lib/api";
import type { ChatEntry, InterviewerMessage } from "@/lib/types";

const SESSION_KEY = "adaptive_interviewer_session_id";
const USER_KEY = "adaptive_interviewer_user_id";

export default function InterviewPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [currentMessage, setCurrentMessage] = useState<InterviewerMessage | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [progressPct, setProgressPct] = useState(0);
  const [phase, setPhase] = useState<string>("phase1");
  const [isComplete, setIsComplete] = useState(false);
  const [outputSummary, setOutputSummary] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const endRef = useRef<HTMLDivElement | null>(null);

  const pushEntry = useCallback((role: "interviewer" | "user", text: string, widget?: InterviewerMessage["widget"]) => {
    setEntries((prev) => [
      ...prev,
      { id: uuid(), role, text, widget: widget ?? null, ts: Date.now() },
    ]);
  }, []);

  const handleMessage = useCallback((msg: InterviewerMessage) => {
    setCurrentMessage(msg);
    pushEntry("interviewer", msg.text, msg.widget);
    setPhase(msg.phase);
    if (msg.is_terminal) {
      setIsComplete(true);
    }
  }, [pushEntry]);

  // Start or resume on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        let userId = localStorage.getItem(USER_KEY);
        if (!userId) {
          userId = uuid();
          localStorage.setItem(USER_KEY, userId);
        }
        const existing = localStorage.getItem(SESSION_KEY);
        if (existing) {
          try {
            const state = await getState(existing);
            if (!cancelled && state.status === "active") {
              setSessionId(existing);
              setPhase(state.phase);
              setProgressPct(state.progress_pct);
              pushEntry("interviewer", "(resumed — continuing from where we left off)");
              return;
            }
          } catch {
            // fall through to new start
          }
        }
        const res = await startInterview(userId);
        if (cancelled) return;
        localStorage.setItem(SESSION_KEY, res.session_id);
        setSessionId(res.session_id);
        handleMessage(res.message);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => { cancelled = true; };
  }, [handleMessage, pushEntry]);

  // Scroll to bottom on new entries.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  // Poll state occasionally for progress.
  useEffect(() => {
    if (!sessionId || isComplete) return;
    const int = window.setInterval(async () => {
      try {
        const st = await getState(sessionId);
        setProgressPct(st.progress_pct);
      } catch { /* ignore */ }
    }, 5000);
    return () => window.clearInterval(int);
  }, [sessionId, isComplete]);

  const submitAnswer = async (payload: { answer_text?: string; answer_structured?: Record<string, unknown> }) => {
    if (!sessionId || submitting) return;
    setSubmitting(true);
    try {
      if (payload.answer_text) pushEntry("user", payload.answer_text);
      else if (payload.answer_structured) pushEntry("user", "[structured response submitted]");
      const res = await postTurn(sessionId, payload);
      handleMessage(res.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const finalize = async () => {
    if (!sessionId) return;
    try {
      const res = await completeInterview(sessionId);
      setOutputSummary(res.output);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    if (isComplete && sessionId && !outputSummary) {
      void finalize();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isComplete, sessionId]);

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col">
      <ProgressBar phase={phase} label={currentMessage?.progress_label} pct={progressPct} />

      <div className="flex-1 overflow-hidden px-4 pt-4">
        <ChatLog entries={entries} />
        <div ref={endRef} />
      </div>

      {error && (
        <div className="mx-4 my-2 rounded-md border border-darpan-error/40 bg-darpan-error/10 px-3 py-2 text-sm text-darpan-error">
          {error}
        </div>
      )}

      <div className="border-t border-darpan-border bg-darpan-bg p-4">
        {isComplete ? (
          <CompletionPanel output={outputSummary} />
        ) : (
          <Composer
            widget={currentMessage?.widget}
            disabled={submitting}
            onSubmitText={(text) => submitAnswer({ answer_text: text })}
            onSubmitStructured={(struct) => submitAnswer({ answer_structured: struct })}
          />
        )}
      </div>
    </main>
  );
}

function CompletionPanel({ output }: { output: Record<string, unknown> | null }) {
  if (!output) {
    return <div className="text-sm text-neutral-400">Finalizing your output…</div>;
  }
  const archetype = (output.archetype as any)?.primary ?? "—";
  const qa = (output.qa as any) ?? {};
  const flags = qa.flags ?? [];
  return (
    <div className="rounded-xl border border-darpan-lime/40 bg-darpan-lime/5 p-4">
      <div className="mb-2 font-mono text-xs uppercase tracking-widest text-darpan-lime">Output</div>
      <div className="mb-1 text-sm">
        <span className="text-neutral-500">Primary archetype: </span>
        <span className="font-semibold text-neutral-100">{String(archetype)}</span>
      </div>
      <div className="mb-1 text-sm">
        <span className="text-neutral-500">Coverage: </span>
        <span className="font-semibold text-neutral-100">{qa.coverage_pct?.toFixed?.(1) ?? "—"}%</span>
      </div>
      {flags.length > 0 && (
        <div className="mt-3">
          <div className="mb-1 text-xs uppercase tracking-widest text-neutral-500">QA flags</div>
          <ul className="list-disc pl-5 text-xs text-neutral-300">
            {flags.map((f: any, i: number) => (
              <li key={i}>
                <span className="text-neutral-500">[{f.severity}]</span> {f.key}: {f.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
      <details className="mt-3">
        <summary className="cursor-pointer text-xs text-neutral-500 hover:text-neutral-300">Raw JSON</summary>
        <pre className="mt-2 max-h-80 overflow-auto rounded-md bg-darpan-elevated p-3 text-[11px] text-neutral-300">
          {JSON.stringify(output, null, 2)}
        </pre>
      </details>
    </div>
  );
}
