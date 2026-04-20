import type { InterviewerMessage } from "./types";

export type StartResponse = { session_id: string; message: InterviewerMessage };
export type TurnResponse  = { session_id: string; message: InterviewerMessage };
export type StateResponse = {
  session_id: string;
  status: string;
  phase: string;
  block?: string | null;
  archetype?: string | null;
  progress_pct: number;
  elapsed_sec: number;
};
export type CompleteResponse = { session_id: string; output: Record<string, unknown>; qa: Record<string, unknown> };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/backend/api/v1${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText} — ${body}`);
  }
  return res.json();
}

export function startInterview(userId: string): Promise<StartResponse> {
  return request<StartResponse>("/adaptive/start", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, input_mode: "text" }),
  });
}

export function postTurn(
  sessionId: string,
  payload: { answer_text?: string; answer_structured?: Record<string, unknown> },
): Promise<TurnResponse> {
  return request<TurnResponse>(`/adaptive/${sessionId}/turn`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getState(sessionId: string): Promise<StateResponse> {
  return request<StateResponse>(`/adaptive/${sessionId}/state`);
}

export function completeInterview(sessionId: string): Promise<CompleteResponse> {
  return request<CompleteResponse>(`/adaptive/${sessionId}/complete`, { method: "POST" });
}
