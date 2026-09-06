#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { prepareFacultyAppend } from "../src/faculty-append.js";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "../..");

function parseArguments(argv) {
  const options = { minimum: 100 };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!new Set(["--batch", "--existing", "--minimum"]).has(argument)) {
      throw new Error(`unknown argument: ${argument}`);
    }
    const value = argv[index + 1];
    if (value === undefined) throw new Error(`missing value for ${argument}`);
    options[argument.slice(2)] = value;
    index += 1;
  }
  if (!options.batch) throw new Error("--batch is required");
  if (!options.existing) throw new Error("--existing is required");
  const minimum = Number(options.minimum);
  if (!Number.isInteger(minimum) || minimum < 0 || minimum > 250) {
    throw new Error("--minimum must be an integer from 0 to 250");
  }
  return { ...options, minimum };
}

function isInsideRepository(candidate) {
  const relative = path.relative(repositoryRoot, candidate);
  return relative === ""
    || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function loadPrivateJson(value, label) {
  const resolved = path.resolve(value);
  if (isInsideRepository(resolved)) {
    throw new Error(`${label} must be stored outside the Git repository`);
  }
  const parsed = JSON.parse(fs.readFileSync(resolved, "utf8"));
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} must contain a JSON object`);
  }
  return parsed;
}

function categoryFor(record) {
  const area = String(record.research_area || "").toLowerCase();
  if (/neuro|brain|cerebell|cognitive/.test(area)) return "Neuroscience";
  if (/complex|network|contagion|epidemic/.test(area)) return "Complex Systems";
  return "Agent/AI4Science";
}

function countsBy(records, selector) {
  const counts = new Map();
  for (const record of records) {
    const key = selector(record);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return Object.fromEntries([...counts].sort(([left], [right]) => left.localeCompare(right)));
}

function main() {
  const options = parseArguments(process.argv.slice(2));
  const batch = loadPrivateJson(options.batch, "batch");
  const existing = loadPrivateJson(options.existing, "existing seed");
  if (!Array.isArray(batch.faculty)) throw new Error("batch.faculty must be an array");
  if (!Array.isArray(existing.faculty)) throw new Error("existing.faculty must be an array");

  const prepared = prepareFacultyAppend(
    existing.faculty,
    batch.faculty,
    new Date().toISOString()
  );
  if (prepared.appended.length < options.minimum) {
    throw new Error(
      `valid new record count ${prepared.appended.length} is below required minimum ${options.minimum}`
    );
  }

  const scores = prepared.appended.map((record) => record.fit.total);
  const summary = {
    submitted: batch.faculty.length,
    validNew: prepared.appended.length,
    localDuplicates: prepared.skipped,
    countryCounts: countsBy(prepared.appended, (record) => record.country),
    categoryCounts: countsBy(prepared.appended, categoryFor),
    scoreRange: {
      min: scores.length ? Math.min(...scores) : null,
      max: scores.length ? Math.max(...scores) : null
    }
  };
  process.stdout.write(`${JSON.stringify(summary)}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : "batch validation failed"}\n`);
  process.exitCode = 1;
}
