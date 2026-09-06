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

function syntheticFaculty() {
  return {
    id: "fac_0123456789ab",
    name: "Synthetic Researcher",
    display_name: "Synthetic Researcher",
    institution: "Example Institute of Technology",
    institution_short: "EIT",
    department: "Department of Computational Science",
    country: "United Kingdom",
    region: "Europe",
    entry_type: "research_group",
    homepage_url: "https://example.edu/lab/",
    word_homepage_url: "https://example.edu/lab/",
    research_area: "AI4Science/LLM",
    research_summary: "Autonomous agents for scientific reasoning and discovery.",
    keywords: ["llm agents", "ai for science"],
    evidence: [{
      title: "Official research group page",
      url: "https://example.edu/lab/",
      checked_on: "2026-09-07T00:00:00Z",
      note: "Official institutional page confirms the current research focus."
    }],
    fit: {
      total: 86,
      confidence: "high",
      dimensions: [{ name: "AI4Science / LLM Agents", matched_terms: ["llm agents"] }]
    },
    match_analysis: { summary: "Strong overlap with agentic scientific reasoning." },
    email_addressee: "Professor Researcher",
    source_document: "Independent official-web research"
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

  it("allows only secret-protected POST requests to the faculty append route", async () => {
    const imported = await SELF.fetch(`${origin}/api/admin/import`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer synthetic-migration-secret-32-bytes"
      },
      body: JSON.stringify(syntheticSeed())
    });
    expect(imported.status).toBe(201);

    expect((await SELF.fetch(`${origin}/api/admin/faculty/append`)).status).toBe(404);
    expect((await SELF.fetch(`${origin}/api/admin/faculty/append`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ faculty: [syntheticFaculty()] })
    })).status).toBe(404);

    const rejected = await SELF.fetch(`${origin}/api/admin/faculty/append`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer incorrect"
      },
      body: JSON.stringify({ faculty: [syntheticFaculty()] })
    });
    expect(rejected.status).toBe(403);

    const accepted = await SELF.fetch(`${origin}/api/admin/faculty/append`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer synthetic-migration-secret-32-bytes"
      },
      body: JSON.stringify({ faculty: [syntheticFaculty()] })
    });
    expect(accepted.status).toBe(200);
    expect(await accepted.json()).toMatchObject({ appended: 1, skipped: 0, facultyTotal: 2 });

    const repeated = await SELF.fetch(`${origin}/api/admin/faculty/append`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer synthetic-migration-secret-32-bytes"
      },
      body: JSON.stringify({ faculty: [syntheticFaculty()] })
    });
    expect(repeated.status).toBe(200);
    expect(await repeated.json()).toMatchObject({
      revision: 2,
      appended: 0,
      skipped: 1,
      facultyTotal: 2
    });
  });
});
