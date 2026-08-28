import { describe, expect, it } from "vitest";
import { jsonResponse, readJson, secureHeaders } from "../src/http.js";

describe("HTTP boundary", () => {
  it("adds restrictive response headers", () => {
    const headers = secureHeaders();
    expect(headers.get("content-security-policy")).toContain("default-src 'self'");
    expect(headers.get("x-content-type-options")).toBe("nosniff");
    expect(headers.get("referrer-policy")).toBe("no-referrer");
  });

  it("rejects JSON bodies larger than the configured limit", async () => {
    const request = new Request("https://agent.test/api", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ value: "x".repeat(100) })
    });
    await expect(readJson(request, 32)).rejects.toThrow("request body too large");
  });

  it("serializes JSON without reflecting secrets into headers", async () => {
    const response = jsonResponse({ ok: true }, 201);
    expect(response.status).toBe(201);
    expect(await response.json()).toEqual({ ok: true });
  });
});
