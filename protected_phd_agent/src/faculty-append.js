const MAX_BATCH = 250;
const MAX_RECORD_BYTES = 75_000;
const FACULTY_ID_PATTERN = /^fac_[a-z0-9]{12,32}$/;
const FORBIDDEN_COUNTRIES = new Set([
  "canada",
  "ca",
  "united states",
  "united states of america",
  "usa",
  "us",
  "u.s.",
  "u.s.a."
]);
const FIT_CONFIDENCE = new Set(["low", "medium", "high"]);
const REQUIRED_STRINGS = [
  "id",
  "name",
  "display_name",
  "institution",
  "institution_short",
  "department",
  "country",
  "region",
  "entry_type",
  "homepage_url",
  "word_homepage_url",
  "research_area",
  "research_summary",
  "email_addressee",
  "source_document"
];

const encoder = new TextEncoder();

function normalizedText(value) {
  return String(value || "").trim().replace(/\s+/g, " ").toLowerCase();
}

function requireString(record, field) {
  if (typeof record[field] !== "string" || !record[field].trim()) {
    throw new Error(`missing required field: ${field}`);
  }
  record[field] = record[field].trim();
}

function validateEvidence(value) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error("first-party evidence required");
  }
  for (const item of value) {
    if (!item || Array.isArray(item) || typeof item !== "object") {
      throw new Error("invalid evidence item");
    }
    for (const field of ["title", "url", "checked_on", "note"]) {
      if (typeof item[field] !== "string" || !item[field].trim()) {
        throw new Error(`invalid evidence field: ${field}`);
      }
    }
    canonicalHttpUrl(item.url);
    if (!Number.isFinite(Date.parse(item.checked_on))) {
      throw new Error("invalid evidence date");
    }
  }
}

function validateFit(value) {
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new Error("invalid fit");
  }
  if (!Number.isInteger(value.total) || value.total < 0 || value.total > 100) {
    throw new Error("invalid fit total");
  }
  if (!FIT_CONFIDENCE.has(value.confidence)) {
    throw new Error("invalid fit confidence");
  }
  if (!Array.isArray(value.dimensions) || value.dimensions.length === 0) {
    throw new Error("fit dimensions required");
  }
}

function validateMatchAnalysis(value) {
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new Error("invalid match analysis");
  }
  if (typeof value.summary !== "string" || !value.summary.trim()) {
    throw new Error("match analysis summary required");
  }
}

function validateFacultyRecord(value, nowIso) {
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new Error("invalid faculty record");
  }

  const record = structuredClone(value);
  for (const field of REQUIRED_STRINGS) requireString(record, field);
  if (!FACULTY_ID_PATTERN.test(record.id)) {
    throw new Error("invalid faculty id");
  }
  if (FORBIDDEN_COUNTRIES.has(normalizedText(record.country))) {
    throw new Error("country is not eligible");
  }

  canonicalHttpUrl(record.homepage_url);
  canonicalHttpUrl(record.word_homepage_url);
  if (!Array.isArray(record.keywords)
    || record.keywords.length === 0
    || record.keywords.some((keyword) => typeof keyword !== "string" || !keyword.trim())) {
    throw new Error("research keywords required");
  }
  validateEvidence(record.evidence);
  validateFit(record.fit);
  validateMatchAnalysis(record.match_analysis);

  delete record.featured_rank;
  record.status = "discovered";
  record.notes = "";
  record.curated_on = nowIso.slice(0, 10);
  record.updated_at = nowIso;

  let serialized;
  try {
    serialized = JSON.stringify(record);
  } catch {
    throw new Error("faculty record is not serializable");
  }
  if (encoder.encode(serialized).byteLength > MAX_RECORD_BYTES) {
    throw new Error("faculty record too large");
  }
  return record;
}

export function canonicalHttpUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error("invalid HTTP(S) URL");
  }
  if (!new Set(["http:", "https:"]).has(url.protocol)) {
    throw new Error("invalid HTTP(S) URL");
  }
  url.hash = "";
  url.hostname = url.hostname.toLowerCase().replace(/^www\./, "");
  url.pathname = url.pathname.replace(/\/+$/, "") || "/";
  return url.href;
}

function homepageKey(record) {
  const value = record?.homepage_url || record?.word_homepage_url;
  if (!value) return "";
  try {
    return canonicalHttpUrl(value);
  } catch {
    return "";
  }
}

function identityKey(record) {
  return `${normalizedText(record?.name || record?.display_name)}|${normalizedText(record?.institution)}`;
}

export function prepareFacultyAppend(existingRecords, submittedRecords, nowIso) {
  if (!Array.isArray(existingRecords)) throw new Error("invalid existing faculty");
  if (!Array.isArray(submittedRecords) || submittedRecords.length === 0) {
    throw new Error("faculty batch must be a non-empty array");
  }
  if (submittedRecords.length > MAX_BATCH) throw new Error("faculty batch too large");
  if (!Number.isFinite(Date.parse(nowIso))) throw new Error("invalid append timestamp");

  const clean = submittedRecords.map((record) => validateFacultyRecord(record, nowIso));
  const submittedIds = new Set();
  for (const record of clean) {
    if (submittedIds.has(record.id)) throw new Error("duplicate submitted faculty id");
    submittedIds.add(record.id);
  }

  const existingIds = new Map(existingRecords.map((record) => [record.id, record]));
  const homepages = new Set(existingRecords.map(homepageKey).filter(Boolean));
  const identities = new Set(existingRecords.map(identityKey));
  const appended = [];
  let skipped = 0;

  for (const record of clean) {
    const existingId = existingIds.get(record.id);
    const homepage = homepageKey(record);
    const identity = identityKey(record);
    if (existingId) {
      if (homepageKey(existingId) === homepage || identityKey(existingId) === identity) {
        skipped += 1;
        continue;
      }
      throw new Error("faculty id already exists");
    }
    if ((homepage && homepages.has(homepage)) || identities.has(identity)) {
      skipped += 1;
      continue;
    }

    appended.push(record);
    existingIds.set(record.id, record);
    if (homepage) homepages.add(homepage);
    identities.add(identity);
  }

  return { appended, skipped };
}

export function prepareFacultyUnfeature(existingRecords, submittedIds) {
  if (!Array.isArray(existingRecords)) throw new Error("invalid existing faculty");
  if (!Array.isArray(submittedIds) || submittedIds.length === 0) {
    throw new Error("faculty id batch must be a non-empty array");
  }
  if (submittedIds.length > MAX_BATCH) throw new Error("faculty id batch too large");

  const seen = new Set();
  for (const id of submittedIds) {
    if (typeof id !== "string" || !FACULTY_ID_PATTERN.test(id)) {
      throw new Error("invalid faculty id");
    }
    if (seen.has(id)) throw new Error("duplicate submitted faculty id");
    seen.add(id);
  }

  const indices = new Map(existingRecords.map((record, index) => [record.id, index]));
  for (const id of submittedIds) {
    if (!indices.has(id)) throw new Error("faculty id not found");
  }

  const faculty = structuredClone(existingRecords);
  let cleared = 0;
  let skipped = 0;
  for (const id of submittedIds) {
    const record = faculty[indices.get(id)];
    if (Number(record.featured_rank) > 0) {
      delete record.featured_rank;
      cleared += 1;
    } else {
      skipped += 1;
    }
  }

  return { faculty, cleared, skipped };
}
