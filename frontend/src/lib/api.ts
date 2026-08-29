import type {
  AbandonedCart,
  Campaign,
  ChatMessage,
  ChatSession,
  ChurnRisk,
  CustomerSegment,
  DashboardSummary,
  LeakFinding,
  SegmentSummary,
  SendMessageResponse,
  TokenResponse,
  UserOut,
  WeeklyReport,
} from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") + "/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  auth: {
    register: (payload: { merchant_name: string; name: string; email: string; password: string; industry?: string }) =>
      request<TokenResponse>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
    login: (payload: { email: string; password: string }) =>
      request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
    me: () => request<UserOut>("/auth/me"),
  },
  analytics: {
    dashboard: () => request<DashboardSummary>("/analytics/dashboard"),
    revenueLeaks: () => request<{ findings: LeakFinding[] }>("/analytics/revenue-leaks"),
    segments: () => request<{ customers: CustomerSegment[]; summary: SegmentSummary[] }>("/analytics/segments"),
    churn: () => request<{ customers: ChurnRisk[] }>("/analytics/churn"),
    abandonedCarts: () => request<{ carts: AbandonedCart[] }>("/analytics/abandoned-carts"),
  },
  campaigns: {
    list: () => request<Campaign[]>("/campaigns"),
    generate: (payload: { campaign_type: string; target_segment?: string }) =>
      request<Campaign>("/campaigns/generate", { method: "POST", body: JSON.stringify(payload) }),
  },
  reports: {
    list: () => request<WeeklyReport[]>("/reports/weekly"),
    generate: () => request<WeeklyReport>("/reports/weekly/generate", { method: "POST" }),
  },
  chat: {
    sessions: () => request<ChatSession[]>("/chat/sessions"),
    messages: (sessionId: string) => request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),
    send: (payload: { session_id?: string; message: string }) =>
      request<SendMessageResponse>("/chat/messages", { method: "POST", body: JSON.stringify(payload) }),
  },
};
