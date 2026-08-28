import { jsonResponse } from "./http.js";
import { validatePatch } from "./validation.js";

const COLLECTIONS = ["faculty", "programs", "applications", "artifacts"];
const encoder = new TextEncoder();

function clone(value) {
  return structuredClone(value);
}

async function digest(value) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(String(value))));
}

async function secretMatches(supplied, expected) {
  const left = await digest(supplied);
  const right = await digest(expected);
  let difference = left.length ^ right.length;
  for (let index = 0; index < Math.max(left.length, right.length); index += 1) {
    difference |= (left[index] || 0) ^ (right[index] || 0);
  }
  return difference === 0;
}

function normalizeSeed(seed) {
  if (!seed || Array.isArray(seed) || typeof seed !== "object") {
    throw new Error("invalid seed");
  }
  if (seed.schemaVersion !== 1) throw new Error("unsupported schema version");
  if (!seed.profile || Array.isArray(seed.profile) || typeof seed.profile !== "object") {
    throw new Error("invalid profile");
  }

  const state = {
    schemaVersion: 1,
    revision: 1,
    updatedAt: new Date().toISOString(),
    profile: clone(seed.profile)
  };
  for (const collection of COLLECTIONS) {
    if (!Array.isArray(seed[collection])) throw new Error(`invalid ${collection}`);
    state[collection] = clone(seed[collection]);
  }
  return state;
}

export class WorkflowCoordinator {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.storage = ctx.storage;
    this.env = env;
  }

  async bootstrap() {
    const state = await this.storage.get("workflow");
    if (!state) return jsonResponse({ error: "workflow not initialized" }, 404);
    return jsonResponse(state);
  }

  async update(collection, id, patch, expectedRevision) {
    const state = await this.storage.get("workflow");
    if (!state) return jsonResponse({ error: "workflow not initialized" }, 404);
    if (!Number.isInteger(expectedRevision) || expectedRevision !== state.revision) {
      return jsonResponse({ error: "revision conflict", revision: state.revision }, 409);
    }

    let cleanPatch;
    try {
      cleanPatch = validatePatch(collection, patch);
    } catch (error) {
      return jsonResponse({ error: error.message }, 400);
    }

    const records = state[collection];
    const index = records.findIndex((record) => record.id === id);
    if (index < 0) return jsonResponse({ error: "record not found" }, 404);

    const next = clone(state);
    next[collection][index] = { ...next[collection][index], ...cleanPatch };
    next.revision += 1;
    next.updatedAt = new Date().toISOString();
    await this.storage.put("workflow", next);
    await this.env.PHD_AGENT_DATA.put("snapshot:latest", JSON.stringify(next));
    return jsonResponse({
      revision: next.revision,
      updatedAt: next.updatedAt,
      record: next[collection][index]
    });
  }

  async importOnce(seed, migrationSecret) {
    if (!this.env.MIGRATION_SECRET
      || !(await secretMatches(migrationSecret || "", this.env.MIGRATION_SECRET))) {
      return jsonResponse({ error: "forbidden" }, 403);
    }
    if (await this.storage.get("migration_complete")) {
      return jsonResponse({ error: "migration already completed" }, 409);
    }

    let state;
    try {
      state = normalizeSeed(seed);
    } catch (error) {
      return jsonResponse({ error: error.message }, 400);
    }

    await this.storage.put("workflow", state);
    await this.storage.put("migration_complete", true);
    await this.env.PHD_AGENT_DATA.put("snapshot:latest", JSON.stringify(state));
    return jsonResponse({ revision: state.revision }, 201);
  }

  async exportSnapshot() {
    const state = await this.storage.get("workflow");
    if (!state) return jsonResponse({ error: "workflow not initialized" }, 404);
    return jsonResponse(state);
  }
}
