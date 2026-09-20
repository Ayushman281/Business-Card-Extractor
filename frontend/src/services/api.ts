import type { Health, Job, Lead, UploadConfig } from "../types/leads";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

// Runtime settings let the same built frontend move between cloud hosts.
let apiOrigin: Promise<string> | undefined;
function backendOrigin(): Promise<string> {
  if (!apiOrigin) {
    apiOrigin = (async () => {
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch("/app-config.json", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Missing runtime configuration");
        const config: unknown = await response.json();
        if (!config || typeof config !== "object" || !("apiBaseUrl" in config) || typeof config.apiBaseUrl !== "string") {
          throw new Error("Invalid runtime configuration");
        }
        const value = config.apiBaseUrl.trim();
        if (!value) return "";
        const url = new URL(value);
        if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
          throw new Error("API address must be an HTTP(S) origin");
        }
        if (window.location.protocol === "https:" && url.protocol !== "https:") {
          throw new Error("An HTTPS frontend requires an HTTPS API");
        }
        return url.origin;
      } finally {
        window.clearTimeout(timer);
      }
    })().catch(() => {
      apiOrigin = undefined;
      throw new ApiError("The application connection settings are unavailable or invalid. Contact the deployment owner.", 0);
    });
  }
  return apiOrigin;
}

async function request(path: string, options: RequestInit = {}, timeout = 15000): Promise<Response> {
  const origin = await backendOrigin();
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(origin + path, { ...options, signal: controller.signal, cache: "no-store" });
    if (!response.ok) {
      let message = response.status === 413
        ? "The upload is too large. Select fewer or smaller images."
        : "The server could not complete the request.";
      try {
        const body: unknown = await response.json();
        if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
          message = body.detail;
        }
      } catch { /* Nginx can return a non-JSON error. */ }
      throw new ApiError(message, response.status);
    }
    return response;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The request timed out. Check your connection and retry.", 0);
    }
    throw new ApiError("Cannot reach the server. Check your connection and retry.", 0);
  } finally {
    window.clearTimeout(timer);
  }
}

export async function health(): Promise<Health> { return (await request("/api/health")).json(); }
export async function config(): Promise<UploadConfig> { return (await request("/api/config")).json(); }
export async function extract(files: File[]): Promise<Job> {
  const body = new FormData();
  files.forEach(file => body.append("files", file));
  return (await request("/api/v1/leads/extract", { method: "POST", body }, 120000)).json();
}
export async function getJob(id: string): Promise<Job> {
  return (await request("/api/v1/leads/jobs/" + encodeURIComponent(id))).json();
}
export async function deleteJob(id: string): Promise<void> {
  await request("/api/v1/leads/jobs/" + encodeURIComponent(id), { method: "DELETE" });
}
export async function exportLeads(leads: Lead[]): Promise<void> {
  const response = await request("/api/v1/leads/export", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ leads }),
  }, 30000);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const header = response.headers.get("Content-Disposition") || "";
  link.download = /filename="([^"]+)"/.exec(header)?.[1] || "business_card_leads.xlsx";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
