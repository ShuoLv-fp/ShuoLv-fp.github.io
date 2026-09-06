import { describe, expect, it } from "vitest";
import { WorkflowCoordinator } from "../src/coordinator.js";
import { validatePatch } from "../src/validation.js";
import { createMemoryStorage } from "./support/memory-storage.js";

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

function syntheticFaculty(overrides = {}) {
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
    source_document: "Independent official-web research",
    ...overrides
  };
}

function coordinatorFixture() {
  const storage = createMemoryStorage();
  const snapshots = [];
  const env = {
    MIGRATION_SECRET: "synthetic-migration-secret-32-bytes",
    WORKFLOW_PASSWORD: "synthetic-test-password",
    SESSION_SECRET: "synthetic-session-secret-with-32-bytes",
    RATE_LIMIT_SECRET: "synthetic-rate-limit-secret-32-bytes",
    PHD_AGENT_DATA: {
      async put(key, value) {
        snapshots.push([key, JSON.parse(value)]);
      }
    }
  };
  return {
    coordinator: new WorkflowCoordinator({ storage }, env),
    snapshots,
    storage
  };
}

describe("workflow mutation schema", () => {
  it("allows only editable outreach fields", () => {
    expect(validatePatch("artifacts", {
      subject: "Revised",
      content: "Body",
      status: "draft"
    })).toEqual({ subject: "Revised", content: "Body", status: "draft" });
    expect(() => validatePatch("artifacts", { target_id: "rewire-target" }))
      .toThrow("field not editable");
  });

  it("rejects oversized email bodies", () => {
    expect(() => validatePatch("artifacts", { content: "x".repeat(50_001) }))
      .toThrow("field too large");
  });
});

describe("WorkflowCoordinator", () => {
  it("uses the trusted public origin when invoked behind a gateway", async () => {
    const { coordinator } = coordinatorFixture();
    const publicOrigin = "https://gateway.pages.dev";
    const response = await coordinator.fetch(new Request(
      "https://coordinator.internal/api/login",
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          origin: publicOrigin,
          "x-phd-agent-origin": publicOrigin
        },
        body: JSON.stringify({ password: "synthetic-test-password" })
      }
    ));

    expect(response.status).toBe(200);
  });

  it("imports once, increments revisions, mirrors snapshots and rejects stale writes", async () => {
    const { coordinator, snapshots } = coordinatorFixture();

    expect((await coordinator.importOnce(syntheticSeed(), "incorrect")).status).toBe(403);
    const imported = await coordinator.importOnce(
      syntheticSeed(),
      "synthetic-migration-secret-32-bytes"
    );
    expect(imported.status).toBe(201);
    expect((await imported.json()).revision).toBe(1);

    const updated = await coordinator.update(
      "artifacts",
      "art_1",
      { subject: "Revised" },
      1
    );
    expect(updated.status).toBe(200);
    expect((await updated.json()).revision).toBe(2);

    const stale = await coordinator.update(
      "artifacts",
      "art_1",
      { subject: "Overwritten" },
      1
    );
    expect(stale.status).toBe(409);

    const exported = await coordinator.exportSnapshot();
    const state = await exported.json();
    expect(state.artifacts[0].subject).toBe("Revised");
    expect(state.revision).toBe(2);
    expect(snapshots).toHaveLength(2);
    expect(snapshots.every(([key]) => key === "snapshot:latest")).toBe(true);
    expect((await coordinator.importOnce(
      syntheticSeed(),
      "synthetic-migration-secret-32-bytes"
    )).status).toBe(409);
  });

  it("requires the migration secret for faculty appends", async () => {
    const { coordinator } = coordinatorFixture();
    await coordinator.importOnce(syntheticSeed(), "synthetic-migration-secret-32-bytes");

    const response = await coordinator.appendFaculty([syntheticFaculty()], "incorrect");

    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ error: "forbidden" });
  });

  it("appends faculty atomically while preserving existing workflow data", async () => {
    const { coordinator, snapshots } = coordinatorFixture();
    await coordinator.importOnce(syntheticSeed(), "synthetic-migration-secret-32-bytes");
    const before = await (await coordinator.exportSnapshot()).json();

    const response = await coordinator.appendFaculty(
      [syntheticFaculty()],
      "synthetic-migration-secret-32-bytes"
    );
    const result = await response.json();
    const after = await (await coordinator.exportSnapshot()).json();

    expect(response.status).toBe(200);
    expect(result).toMatchObject({
      revision: 2,
      submitted: 1,
      appended: 1,
      skipped: 0,
      previousFacultyTotal: 1,
      facultyTotal: 2,
      featuredTotal: 0,
      artifactTotal: 1
    });
    expect(after.revision).toBe(before.revision + 1);
    expect(after.faculty[0]).toEqual(before.faculty[0]);
    expect(after.faculty[1]).toMatchObject({
      id: "fac_0123456789ab",
      status: "discovered",
      notes: ""
    });
    expect(after.faculty[1]).not.toHaveProperty("featured_rank");
    expect(after.profile).toEqual(before.profile);
    expect(after.programs).toEqual(before.programs);
    expect(after.applications).toEqual(before.applications);
    expect(after.artifacts).toEqual(before.artifacts);
    expect(snapshots).toHaveLength(2);
  });

  it("makes repeated faculty appends idempotent without changing the revision", async () => {
    const { coordinator, snapshots } = coordinatorFixture();
    await coordinator.importOnce(syntheticSeed(), "synthetic-migration-secret-32-bytes");
    await coordinator.appendFaculty(
      [syntheticFaculty()],
      "synthetic-migration-secret-32-bytes"
    );

    const response = await coordinator.appendFaculty(
      [syntheticFaculty()],
      "synthetic-migration-secret-32-bytes"
    );
    const result = await response.json();

    expect(response.status).toBe(200);
    expect(result).toMatchObject({
      revision: 2,
      submitted: 1,
      appended: 0,
      skipped: 1,
      previousFacultyTotal: 2,
      facultyTotal: 2,
      featuredTotal: 0,
      artifactTotal: 1
    });
    expect(snapshots).toHaveLength(2);
  });

  it("rejects the whole faculty batch when any record is invalid", async () => {
    const { coordinator, snapshots } = coordinatorFixture();
    await coordinator.importOnce(syntheticSeed(), "synthetic-migration-secret-32-bytes");

    const response = await coordinator.appendFaculty(
      [syntheticFaculty(), syntheticFaculty({ id: "fac_badrecord0001", country: "Canada" })],
      "synthetic-migration-secret-32-bytes"
    );
    const after = await (await coordinator.exportSnapshot()).json();

    expect(response.status).toBe(400);
    expect(after.faculty).toHaveLength(1);
    expect(after.revision).toBe(1);
    expect(snapshots).toHaveLength(1);
  });

  it("unfeatures an exact faculty batch atomically and idempotently", async () => {
    const { coordinator, snapshots } = coordinatorFixture();
    const seed = syntheticSeed();
    seed.faculty = [
      { id: "fac_aaaaaaaaaaaa", name: "Existing Featured", featured_rank: 1, notes: "" },
      { id: "fac_bbbbbbbbbbbb", name: "Uploaded Featured", featured_rank: 2, notes: "" },
      { id: "fac_cccccccccccc", name: "Uploaded Plain", notes: "" }
    ];
    await coordinator.importOnce(seed, "synthetic-migration-secret-32-bytes");

    const response = await coordinator.unfeatureFaculty(
      ["fac_bbbbbbbbbbbb", "fac_cccccccccccc"],
      "synthetic-migration-secret-32-bytes"
    );
    const result = await response.json();
    const after = await (await coordinator.exportSnapshot()).json();

    expect(response.status).toBe(200);
    expect(result).toMatchObject({
      revision: 2,
      submitted: 2,
      cleared: 1,
      skipped: 1,
      facultyTotal: 3,
      featuredTotal: 1,
      artifactTotal: 1
    });
    expect(after.faculty[0].featured_rank).toBe(1);
    expect(after.faculty[1]).not.toHaveProperty("featured_rank");
    expect(after.faculty[2]).not.toHaveProperty("featured_rank");

    const repeated = await coordinator.unfeatureFaculty(
      ["fac_bbbbbbbbbbbb", "fac_cccccccccccc"],
      "synthetic-migration-secret-32-bytes"
    );
    expect(await repeated.json()).toMatchObject({ revision: 2, cleared: 0, skipped: 2 });
    expect(snapshots).toHaveLength(2);
  });

  it("rejects an unfeature batch with a missing faculty id without writing", async () => {
    const { coordinator, snapshots } = coordinatorFixture();
    const seed = syntheticSeed();
    seed.faculty = [{ id: "fac_aaaaaaaaaaaa", name: "Featured", featured_rank: 1, notes: "" }];
    await coordinator.importOnce(seed, "synthetic-migration-secret-32-bytes");

    const response = await coordinator.unfeatureFaculty(
      ["fac_aaaaaaaaaaaa", "fac_missing00000"],
      "synthetic-migration-secret-32-bytes"
    );
    const after = await (await coordinator.exportSnapshot()).json();

    expect(response.status).toBe(400);
    expect(after.faculty[0].featured_rank).toBe(1);
    expect(after.revision).toBe(1);
    expect(snapshots).toHaveLength(1);
  });
});
