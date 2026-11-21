import type { CloneMatch, Repository, Scan } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload?.error?.message ?? `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  repositories: () => request<{ items: Repository[] }>("/repositories"),
  createRepository: (name: string, localPath: string) =>
    request<Repository>("/repositories", { method: "POST", body: JSON.stringify({ name, localPath }) }),
  startScan: (repositoryId: string) =>
    request<Scan>("/scans", { method: "POST", body: JSON.stringify({ repositoryId }) }),
  scan: (id: string) => request<Scan>(`/scans/${id}`),
  clones: (repositoryId: string, type?: string) =>
    request<{ items: CloneMatch[] }>(`/clones?repository=${encodeURIComponent(repositoryId)}${type ? `&type=${type}` : ""}`),
  clone: (id: string) => request<CloneMatch>(`/clones/${id}`),
};
