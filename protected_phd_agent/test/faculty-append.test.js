import { describe, expect, it } from "vitest";
import {
  canonicalHttpUrl,
  prepareFacultyAppend,
  prepareFacultyUnfeature
} from "../src/faculty-append.js";

function validFaculty(overrides = {}) {
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
      dimensions: [{
        name: "AI4Science / LLM Agents",
        score: 41,
        weight: 0.45,
        matched_terms: ["llm agents", "scientific reasoning"]
      }]
    },
    match_analysis: {
      summary: "Strong overlap with agentic scientific reasoning.",
      overlap: ["LLM agents"],
      cautions: ["Neuroimaging is not a central focus."]
    },
    email_addressee: "Professor Researcher",
    source_document: "Independent official-web research",
    status: "shortlisted",
    notes: "This submitted note must not be trusted.",
    featured_rank: 2,
    curated_on: "2020-01-01",
    updated_at: "2020-01-01T00:00:00Z",
    ...overrides
  };
}

describe("canonicalHttpUrl", () => {
  it("normalizes host casing, www, fragments and a trailing slash", () => {
    expect(canonicalHttpUrl("HTTPS://WWW.Example.edu/lab/#people"))
      .toBe("https://example.edu/lab");
  });

  it("rejects non-HTTP protocols", () => {
    expect(() => canonicalHttpUrl("javascript:alert(1)"))
      .toThrow("invalid HTTP(S) URL");
  });
});

describe("prepareFacultyAppend", () => {
  it("prepares a valid record without changing featured curation", () => {
    const result = prepareFacultyAppend([
      validFaculty({
        id: "fac_existing0001",
        name: "Existing Researcher",
        display_name: "Existing Researcher",
        institution: "Another Institute",
        homepage_url: "https://another.example.edu/lab",
        word_homepage_url: "https://another.example.edu/lab",
        featured_rank: 28
      })
    ], [validFaculty()], "2026-09-07T00:00:00.000Z");

    expect(result.skipped).toBe(0);
    expect(result.appended).toHaveLength(1);
    expect(result.appended[0]).toMatchObject({
      status: "discovered",
      notes: "",
      curated_on: "2026-09-07",
      updated_at: "2026-09-07T00:00:00.000Z"
    });
    expect(result.appended[0]).not.toHaveProperty("featured_rank");
  });

  it.each(["United States", "USA", "U.S.", "Canada", "CA"])(
    "rejects a forbidden country alias: %s",
    (country) => {
      expect(() => prepareFacultyAppend([], [validFaculty({ country })], "2026-09-07T00:00:00Z"))
        .toThrow("country is not eligible");
    }
  );

  it("rejects an empty batch", () => {
    expect(() => prepareFacultyAppend([], [], "2026-09-07T00:00:00Z"))
      .toThrow("faculty batch must be a non-empty array");
  });

  it("rejects a batch larger than 250 records", () => {
    const records = Array.from({ length: 251 }, (_, index) => validFaculty({
      id: `fac_${index.toString(16).padStart(12, "0")}`,
      name: `Researcher ${index}`,
      display_name: `Researcher ${index}`,
      homepage_url: `https://example.edu/lab/${index}`,
      word_homepage_url: `https://example.edu/lab/${index}`
    }));

    expect(() => prepareFacultyAppend([], records, "2026-09-07T00:00:00Z"))
      .toThrow("faculty batch too large");
  });

  it("rejects missing required identity fields", () => {
    expect(() => prepareFacultyAppend(
      [],
      [validFaculty({ institution: "" })],
      "2026-09-07T00:00:00Z"
    )).toThrow("missing required field: institution");
  });

  it("rejects fit totals outside the 0-100 range", () => {
    expect(() => prepareFacultyAppend(
      [],
      [validFaculty({ fit: { total: 101, confidence: "high", dimensions: [{}] } })],
      "2026-09-07T00:00:00Z"
    )).toThrow("invalid fit total");
  });

  it("rejects records without first-party evidence", () => {
    expect(() => prepareFacultyAppend(
      [],
      [validFaculty({ evidence: [] })],
      "2026-09-07T00:00:00Z"
    )).toThrow("first-party evidence required");
  });

  it("rejects duplicate submitted identifiers", () => {
    const second = validFaculty({
      name: "Second Researcher",
      display_name: "Second Researcher",
      homepage_url: "https://example.edu/second",
      word_homepage_url: "https://example.edu/second"
    });

    expect(() => prepareFacultyAppend(
      [],
      [validFaculty(), second],
      "2026-09-07T00:00:00Z"
    )).toThrow("duplicate submitted faculty id");
  });

  it("rejects an identifier collision with a different existing record", () => {
    const existing = validFaculty({
      name: "Existing Researcher",
      display_name: "Existing Researcher",
      homepage_url: "https://example.edu/existing",
      word_homepage_url: "https://example.edu/existing"
    });

    expect(() => prepareFacultyAppend(
      [existing],
      [validFaculty()],
      "2026-09-07T00:00:00Z"
    )).toThrow("faculty id already exists");
  });

  it("skips an existing canonical homepage", () => {
    const result = prepareFacultyAppend([
      validFaculty({
        id: "fac_existing0002",
        homepage_url: "https://www.example.edu/lab/#overview"
      })
    ], [validFaculty()], "2026-09-07T00:00:00Z");

    expect(result).toEqual({ appended: [], skipped: 1 });
  });

  it("skips an existing normalized name and institution", () => {
    const result = prepareFacultyAppend([
      validFaculty({
        id: "fac_existing0003",
        name: "  SYNTHETIC   RESEARCHER ",
        institution: "example institute OF technology",
        homepage_url: "https://example.edu/other"
      })
    ], [validFaculty()], "2026-09-07T00:00:00Z");

    expect(result).toEqual({ appended: [], skipped: 1 });
  });

  it("makes an exact resubmission idempotent", () => {
    const existing = validFaculty({ featured_rank: 81 });
    const result = prepareFacultyAppend(
      [existing],
      [validFaculty()],
      "2026-09-07T00:00:00Z"
    );

    expect(result).toEqual({ appended: [], skipped: 1 });
  });
});

describe("prepareFacultyUnfeature", () => {
  it("removes featured ranks only from the submitted faculty identifiers", () => {
    const plain = validFaculty({
      id: "fac_cccccccccccc",
      name: "Third Researcher",
      display_name: "Third Researcher",
      institution: "Third Institute",
      homepage_url: "https://third.example.edu/lab",
      word_homepage_url: "https://third.example.edu/lab"
    });
    delete plain.featured_rank;
    const existing = [
      validFaculty({ id: "fac_aaaaaaaaaaaa", featured_rank: 4 }),
      validFaculty({
        id: "fac_bbbbbbbbbbbb",
        name: "Second Researcher",
        display_name: "Second Researcher",
        institution: "Second Institute",
        homepage_url: "https://second.example.edu/lab",
        word_homepage_url: "https://second.example.edu/lab",
        featured_rank: 5
      }),
      plain
    ];

    const result = prepareFacultyUnfeature(existing, ["fac_bbbbbbbbbbbb", "fac_cccccccccccc"]);

    expect(result.cleared).toBe(1);
    expect(result.skipped).toBe(1);
    expect(result.faculty[0].featured_rank).toBe(4);
    expect(result.faculty[1]).not.toHaveProperty("featured_rank");
    expect(result.faculty[2]).not.toHaveProperty("featured_rank");
    expect(existing[1].featured_rank).toBe(5);
  });

  it("rejects the whole operation when a submitted identifier is missing", () => {
    const existing = [validFaculty({ id: "fac_aaaaaaaaaaaa", featured_rank: 4 })];

    expect(() => prepareFacultyUnfeature(existing, ["fac_aaaaaaaaaaaa", "fac_missing00000"]))
      .toThrow("faculty id not found");
    expect(existing[0].featured_rank).toBe(4);
  });

  it("rejects duplicate identifiers", () => {
    expect(() => prepareFacultyUnfeature([], ["fac_aaaaaaaaaaaa", "fac_aaaaaaaaaaaa"]))
      .toThrow("duplicate submitted faculty id");
  });
});
