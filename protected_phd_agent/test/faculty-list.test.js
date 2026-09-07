import { describe, expect, it } from "vitest";
import { orderFaculty } from "../public/faculty-list.js";

describe("orderFaculty", () => {
  it("shows every record with featured faculty first and the rest by fit", () => {
    const records = [
      { id: "plain-low", name: "Alpha", fit: { total: 82 } },
      { id: "featured-two", name: "Delta", featured_rank: 2, fit: { total: 99 } },
      { id: "plain-high", name: "Beta", fit: { total: 98 } },
      { id: "featured-one", name: "Gamma", featured_rank: 1, fit: { total: 80 } }
    ];

    expect(orderFaculty(records).map((record) => record.id)).toEqual([
      "featured-one", "featured-two", "plain-high", "plain-low"
    ]);
    expect(records.map((record) => record.id)).toEqual([
      "plain-low", "featured-two", "plain-high", "featured-one"
    ]);
  });

  it("uses display name and institution as deterministic tie breakers", () => {
    const records = [
      { id: "z", display_name: "Same", institution: "Zurich", fit: { total: 90 } },
      { id: "b", display_name: "Beta", institution: "Berlin", fit: { total: 90 } },
      { id: "a", display_name: "Same", institution: "Amsterdam", fit: { total: 90 } }
    ];

    expect(orderFaculty(records).map((record) => record.id)).toEqual(["b", "a", "z"]);
  });
});
