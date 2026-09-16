import type {
  Application,
  ApplicationEvent,
  ApplicationInput,
  ApplicationPage,
  ApplicationStatus,
  Company,
  EventType,
  User,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  requestId?: string;

  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.status = status;
    this.requestId = requestId;
  }
}

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Request-ID", crypto.randomUUID());
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (response.status === 204) return undefined as T;

  const body = await response.json().catch(() => null) as { detail?: string | Array<{ msg: string }>; request_id?: string } | null;
  if (!response.ok) {
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(". ")
      : detail || "The request could not be completed.";
    throw new ApiError(message, response.status, body?.request_id);
  }
  return body as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: (token: string) => request<User>("/auth/me", {}, token),
  companies: (token: string) => request<Company[]>("/companies", {}, token),
  createCompany: (token: string, data: { name: string; website?: string; industry?: string; location?: string }) =>
    request<Company>("/companies", { method: "POST", body: JSON.stringify(data) }, token),
  applications: (token: string, filters: { search?: string; status?: ApplicationStatus | "" }) => {
    const params = new URLSearchParams({ limit: "100", sort_by: "updated_at", sort_order: "desc" });
    if (filters.search) params.set("search", filters.search);
    if (filters.status) params.set("status", filters.status);
    return request<ApplicationPage>(`/applications?${params}`, {}, token);
  },
  createApplication: (token: string, data: ApplicationInput) =>
    request<Application>("/applications", { method: "POST", body: JSON.stringify(data) }, token),
  updateApplication: (token: string, id: string, data: Partial<ApplicationInput>) =>
    request<Application>(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }, token),
  deleteApplication: (token: string, id: string) =>
    request<void>(`/applications/${id}`, { method: "DELETE" }, token),
  events: (token: string, applicationId: string) =>
    request<ApplicationEvent[]>(`/applications/${applicationId}/events`, {}, token),
  createEvent: (token: string, applicationId: string, event_type: EventType, notes: string) =>
    request<ApplicationEvent>(`/applications/${applicationId}/events`, {
      method: "POST",
      body: JSON.stringify({ event_type, notes }),
    }, token),
};
