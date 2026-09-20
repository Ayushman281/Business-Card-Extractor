export const fields = [
  ["first_name", "First name"], ["last_name", "Last name"],
  ["job_title", "Position / Job title"], ["company", "Company"],
  ["location", "Location"], ["phone", "Phone number"], ["email", "Email address"],
] as const;

export type LeadField = (typeof fields)[number][0];
export type Lead = Record<LeadField, string | null>;
export interface CardResult {
  index: number;
  source_filename: string;
  status: "success" | "error";
  lead: Lead | null;
  error: string | null;
  warnings: string[];
  processing_time_ms: number;
}
export interface Job {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  total: number;
  processed: number;
  successful: number;
  failed: number;
  processing_time_seconds: number;
  leads: CardResult[];
  error: string | null;
}
export interface Health {
  status: string;
  model_loaded: boolean;
  model_state: "disabled" | "loading" | "ready" | "failed";
}
export interface UploadConfig {
  max_files: number;
  max_upload_mb: number;
  job_ttl_seconds: number;
  accepted_extensions: string[];
}
