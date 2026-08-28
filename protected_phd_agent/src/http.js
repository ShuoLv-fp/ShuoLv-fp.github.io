export function secureHeaders() {
  return new Headers({
    "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store"
  });
}

export function jsonResponse(payload, status = 200, extraHeaders = {}) {
  const headers = secureHeaders();
  headers.set("Content-Type", "application/json; charset=utf-8");
  for (const [key, value] of Object.entries(extraHeaders)) {
    headers.set(key, value);
  }
  return new Response(JSON.stringify(payload), { status, headers });
}

export async function readJson(request, maxBytes = 1_048_576) {
  const length = Number(request.headers.get("content-length") || 0);
  if (length > maxBytes) {
    throw new Error("request body too large");
  }

  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > maxBytes) {
    throw new Error("request body too large");
  }

  const value = JSON.parse(text);
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new Error("expected JSON object");
  }
  return value;
}
