import { describe, expect, it } from "vitest";
import { createMemoryStorage } from "./support/memory-storage.js";
import {
  MAX_FAILURES,
  SESSION_TTL_SECONDS,
  authenticate,
  login,
  logout,
  requireMutationGuards
} from "../src/auth.js";

const env = {
  WORKFLOW_PASSWORD: "synthetic-test-password",
  SESSION_SECRET: "synthetic-session-secret-with-32-bytes",
  RATE_LIMIT_SECRET: "synthetic-rate-limit-secret-32-bytes"
};

function loginRequest(password, address = "203.0.113.9") {
  return new Request("https://agent.test/api/login", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "cf-connecting-ip": address
    },
    body: JSON.stringify({ password })
  });
}

describe("authentication", () => {
  it("issues a secure twelve-hour session for the correct password", async () => {
    const storage = createMemoryStorage();
    const before = Date.now();
    const response = await login(loginRequest("synthetic-test-password"), env, storage);
    const payload = await response.json();

    expect(response.status).toBe(200);
    expect(response.headers.get("set-cookie")).toMatch(
      /phd_session=[^;]+; Path=\/; HttpOnly; Secure; SameSite=Strict; Max-Age=43200/
    );
    expect(payload.csrf).toBeTypeOf("string");
    expect(payload.expiresAt).toBeGreaterThanOrEqual(before + SESSION_TTL_SECONDS * 1000);
  });

  it("authenticates the issued cookie and invalidates it on logout", async () => {
    const storage = createMemoryStorage();
    const loginResponse = await login(loginRequest("synthetic-test-password"), env, storage);
    const cookie = loginResponse.headers.get("set-cookie").split(";", 1)[0];
    const request = new Request("https://agent.test/api/session", { headers: { cookie } });

    const session = await authenticate(request, env, storage);
    expect(session?.csrf).toBeTypeOf("string");

    const logoutResponse = await logout(request, env, storage);
    expect(logoutResponse.headers.get("set-cookie")).toContain("Max-Age=0");
    expect(await authenticate(request, env, storage)).toBeNull();
  });

  it("locks an address after five failed attempts without storing the raw address", async () => {
    const storage = createMemoryStorage();
    const address = "203.0.113.10";
    for (let attempt = 0; attempt < MAX_FAILURES; attempt += 1) {
      await login(loginRequest("incorrect", address), env, storage);
    }

    const blocked = await login(loginRequest("synthetic-test-password", address), env, storage);
    expect(blocked.status).toBe(429);
    expect([...storage.dump().keys()].join("\n")).not.toContain(address);
  });

  it("requires matching origin and CSRF for a mutation", () => {
    const accepted = new Request("https://agent.test/api/artifacts/a1", {
      method: "PUT",
      headers: { origin: "https://agent.test", "x-csrf-token": "csrf-1" }
    });
    const wrongOrigin = new Request("https://agent.test/api/artifacts/a1", {
      method: "PUT",
      headers: { origin: "https://elsewhere.test", "x-csrf-token": "csrf-1" }
    });

    expect(requireMutationGuards(accepted, { csrf: "csrf-1" }, "https://agent.test")).toBe(true);
    expect(requireMutationGuards(wrongOrigin, { csrf: "csrf-1" }, "https://agent.test")).toBe(false);
  });
});
