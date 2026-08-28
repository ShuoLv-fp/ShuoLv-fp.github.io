import { jsonResponse, readJson } from "./http.js";

export const SESSION_TTL_SECONDS = 43_200;
export const LOCK_WINDOW_SECONDS = 900;
export const MAX_FAILURES = 5;

const SESSION_COOKIE = "phd_session";
const encoder = new TextEncoder();

function bytesToHex(bytes) {
  return [...new Uint8Array(bytes)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

async function hmac(secret, value) {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  return bytesToHex(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
}

function constantTimeEqual(left, right) {
  const leftBytes = encoder.encode(String(left));
  const rightBytes = encoder.encode(String(right));
  const length = Math.max(leftBytes.length, rightBytes.length);
  let difference = leftBytes.length ^ rightBytes.length;
  for (let index = 0; index < length; index += 1) {
    difference |= (leftBytes[index] || 0) ^ (rightBytes[index] || 0);
  }
  return difference === 0;
}

function cookieValue(request, name) {
  const header = request.headers.get("cookie") || "";
  for (const part of header.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

function sessionCookie(value, maxAge) {
  return `${SESSION_COOKIE}=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`;
}

async function signedSessionValue(sessionId, secret) {
  return `${sessionId}.${await hmac(secret, sessionId)}`;
}

async function sessionIdFromRequest(request, secret) {
  const value = cookieValue(request, SESSION_COOKIE);
  if (!value) return null;
  const separator = value.lastIndexOf(".");
  if (separator < 1) return null;
  const sessionId = value.slice(0, separator);
  const signature = value.slice(separator + 1);
  const expected = await hmac(secret, sessionId);
  return constantTimeEqual(signature, expected) ? sessionId : null;
}

export async function authenticate(request, env, storage) {
  if (!env.SESSION_SECRET) return null;
  const sessionId = await sessionIdFromRequest(request, env.SESSION_SECRET);
  if (!sessionId) return null;

  const session = await storage.get(`session:${sessionId}`);
  if (!session || !Number.isFinite(session.expiresAt)) return null;
  if (session.expiresAt <= Date.now()) {
    await storage.delete(`session:${sessionId}`);
    return null;
  }
  return { sessionId, ...session };
}

export async function login(request, env, storage) {
  if (!env.WORKFLOW_PASSWORD || !env.SESSION_SECRET || !env.RATE_LIMIT_SECRET) {
    return jsonResponse({ error: "authentication is not configured" }, 503);
  }

  let body;
  try {
    body = await readJson(request, 8_192);
  } catch {
    return jsonResponse({ error: "invalid request" }, 400);
  }

  const clientAddress = request.headers.get("cf-connecting-ip") || "unknown";
  const rateKey = `rate:${await hmac(env.RATE_LIMIT_SECRET, clientAddress)}`;
  const now = Date.now();
  let rate = await storage.get(rateKey);
  if (!rate || now - rate.windowStartedAt >= LOCK_WINDOW_SECONDS * 1000) {
    rate = { failures: 0, windowStartedAt: now, lockedUntil: 0 };
  }

  if (rate.lockedUntil > now) {
    return jsonResponse({ error: "too many attempts" }, 429, {
      "Retry-After": String(Math.ceil((rate.lockedUntil - now) / 1000))
    });
  }

  const suppliedDigest = await hmac(env.SESSION_SECRET, String(body.password || ""));
  const expectedDigest = await hmac(env.SESSION_SECRET, env.WORKFLOW_PASSWORD);
  if (!constantTimeEqual(suppliedDigest, expectedDigest)) {
    rate.failures += 1;
    if (rate.failures >= MAX_FAILURES) {
      rate.lockedUntil = now + LOCK_WINDOW_SECONDS * 1000;
    }
    await storage.put(rateKey, rate);
    return jsonResponse(
      { error: rate.lockedUntil ? "too many attempts" : "invalid credentials" },
      rate.lockedUntil ? 429 : 401,
      rate.lockedUntil ? { "Retry-After": String(LOCK_WINDOW_SECONDS) } : {}
    );
  }

  await storage.delete(rateKey);
  const sessionId = crypto.randomUUID();
  const session = {
    csrf: `${crypto.randomUUID()}${crypto.randomUUID()}`,
    expiresAt: now + SESSION_TTL_SECONDS * 1000
  };
  await storage.put(`session:${sessionId}`, session);
  const cookie = await signedSessionValue(sessionId, env.SESSION_SECRET);
  return jsonResponse(session, 200, {
    "Set-Cookie": sessionCookie(cookie, SESSION_TTL_SECONDS)
  });
}

export async function logout(request, env, storage) {
  const session = await authenticate(request, env, storage);
  if (session) {
    await storage.delete(`session:${session.sessionId}`);
  }
  return jsonResponse({ ok: true }, 200, {
    "Set-Cookie": sessionCookie("", 0)
  });
}

export function requireMutationGuards(request, session, expectedOrigin) {
  if (!session || !expectedOrigin) return false;
  return request.headers.get("origin") === expectedOrigin
    && constantTimeEqual(request.headers.get("x-csrf-token") || "", session.csrf || "");
}
