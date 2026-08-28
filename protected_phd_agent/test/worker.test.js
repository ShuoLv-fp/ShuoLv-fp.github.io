import { SELF, reset } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";

const origin = "https://agent.test";

function syntheticSeed() {
  return {
    schemaVersion: 1,
    revision: 0,
    updatedAt: "2026-08-29T00:00:00.000Z",
    profile: { name: "Synthetic Applicant" },
    faculty: [{ id: "fac_1", name: "Synthetic Advisor", notes: "" }],
    programs: [],
    applications: [],
    artifacts: [{ id: "art_1", subject: "Original", content: "Draft", status: "draft" }]
  };
}

async function authenticatedSession() {
  const response = await SELF.fetch(`${origin}/api/login`, {
    method: "POST",
    headers: { "content-type": "application/json", origin },
    body: JSON.stringify({ password: "synthetic-test-password" })
  });
  const payload = await response.json();
  return {
    cookie: response.headers.get("set-cookie").split(";", 1)[0],
    csrf: payload.csrf
  };
}

describe("protected Worker", () => {
  beforeEach(async () => {
    await reset();
  });

  it("does not expose workflow assets or data before login", async () => {
    expect((await SELF.fetch(`${origin}/`)).status).toBe(200);
    expect((await SELF.fetch(`${origin}/login.js`)).status).toBe(200);
    expect((await SELF.fetch(`${origin}/app`)).status).toBe(401);
    expect((await SELF.fetch(`${origin}/app.js`)).status).toBe(401);
    expect((await SELF.fetch(`${origin}/api/bootstrap`)).status).toBe(401);
    expect((await SELF.fetch(`${origin}/data/faculty.json`)).status).toBe(404);
  });

  it("contains no email sending route", async () => {
    const response = await SELF.fetch(`${origin}/api/send`, { method: "POST" });
    expect(response.status).toBe(404);
  });

  it("creates a session but exposes no uninitialized workflow", async () => {
    const wrong = await SELF.fetch(`${origin}/api/login`, {
      method: "POST",
      headers: { "content-type": "application/json", origin },
      body: JSON.stringify({ password: "incorrect" })
    });
    expect(wrong.status).toBe(401);

    const { cookie } = await authenticatedSession();
    expect((await SELF.fetch(`${origin}/api/session`, { headers: { cookie } })).status).toBe(200);
    expect((await SELF.fetch(`${origin}/api/bootstrap`, { headers: { cookie } })).status).toBe(404);
  });

  it("requires the migration secret and CSRF before accepting writes", async () => {
    const rejectedImport = await SELF.fetch(`${origin}/api/admin/import`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer incorrect" },
      body: JSON.stringify(syntheticSeed())
    });
    expect(rejectedImport.status).toBe(403);

    const imported = await SELF.fetch(`${origin}/api/admin/import`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer synthetic-migration-secret-32-bytes"
      },
      body: JSON.stringify(syntheticSeed())
    });
    expect(imported.status).toBe(201);

    const { cookie, csrf } = await authenticatedSession();
    const missingCsrf = await SELF.fetch(`${origin}/api/artifacts/art_1`, {
      method: "PUT",
      headers: { cookie, "content-type": "application/json", origin },
      body: JSON.stringify({ expectedRevision: 1, patch: { subject: "Revised" } })
    });
    expect(missingCsrf.status).toBe(403);

    const accepted = await SELF.fetch(`${origin}/api/artifacts/art_1`, {
      method: "PUT",
      headers: {
        cookie,
        "content-type": "application/json",
        origin,
        "x-csrf-token": csrf
      },
      body: JSON.stringify({ expectedRevision: 1, patch: { subject: "Revised" } })
    });
    expect(accepted.status).toBe(200);
    expect((await accepted.json()).revision).toBe(2);
  });
});
