export type ApplicationStatus =
  | "saved"
  | "applied"
  | "screening"
  | "interview"
  | "technical_interview"
  | "final_interview"
  | "offer"
  | "accepted"
  | "rejected"
  | "withdrawn";

export type EventType =
  | "created"
  | "status_changed"
  | "interview_scheduled"
  | "interview_completed"
  | "offer_received"
  | "note_added";

export interface User {
  id: string;
  email: string;
  is_active: boolean;
}

export interface Company {
  id: string;
  name: string;
  website: string | null;
  industry: string | null;
  location: string | null;
}

export interface Application {
  id: string;
  company_id: string;
  position: string;
  status: ApplicationStatus;
  source: string | null;
  work_model: string | null;
  location: string | null;
  job_url: string | null;
  salary_min: string | null;
  salary_max: string | null;
  currency: string | null;
  applied_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationPage {
  items: Application[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApplicationEvent {
  id: string;
  event_type: EventType;
  from_status: ApplicationStatus | null;
  to_status: ApplicationStatus | null;
  occurred_at: string;
  notes: string | null;
}

export interface ApplicationInput {
  company_id: string;
  position: string;
  status: ApplicationStatus;
  source?: string | null;
  work_model?: string | null;
  location?: string | null;
  job_url?: string | null;
  notes?: string | null;
}
