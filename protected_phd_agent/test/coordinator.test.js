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

function coordinatorFixture() {
  const storage = createMemoryStorage();
  const snapshots = [];
  const env = {
    MIGRATION_SECRET: "synthetic-migration-secret-32-bytes",
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
});
