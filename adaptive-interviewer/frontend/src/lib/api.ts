// HTTP client for the adaptive-interviewer backend.
// Base URL is resolved via Next's rewrite rule -> /api/backend/*

export type InterviewerMessage = {
  phase: string;
  block?: string | null;
  item_id?: string | null;
  text: string;
  widget?: Record<string, unknown> | null;
  progress_label?: string | null;
  is_terminal: boolean;
};

export type StartResponse = {
  session_id: string;
  message: InterviewerMessage;
};

export type TurnResponse = {
  session_id: string;
  message: InterviewerMessage;
};

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

export function completeInterview(sessionId: string) {
  return request<Record<string, unknown>>(`/adaptive/${sessionId}/complete`, {
    method: "POST",
  });
}
