import { getToken, clearToken } from "@/lib/token";

export const UNAUTHORIZED_EVENT = "matchup:unauthorized";

// Fetch wrapper for relative /api URLs. Adds the Bearer token, returns parsed
// JSON (or null for 204) and throws Error(detail) on failure. A 401 clears the
// stored token and notifies the auth provider.
export async function api(path, { method = "GET", body, headers } = {}) {
  const token = getToken();
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Check your connection and try again.");
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
      }
    }
    const data = await response.json().catch(() => ({}));
    let message = data.detail;
    if (Array.isArray(message)) {
      // FastAPI validation errors come as a list of {msg, loc}
      message = message.map((e) => e.msg).join(", ");
    }
    const error = new Error(message || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;
  return response.json().catch(() => null);
}
