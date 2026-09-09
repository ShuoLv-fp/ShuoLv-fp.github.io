"use strict";

process.env.TZ = "Asia/Shanghai";

const test = require("node:test");
const assert = require("node:assert/strict");
const PaperFeed = require("../../assets/js/paper-feed.js");

const today = new Date("2026-09-09T12:00:00+08:00");

test("latest window contains exactly seven calendar dates", () => {
  const start = PaperFeed.parseStart("", today);
  assert.equal(PaperFeed.isoDate(start), "2026-09-03");
  const records = [
    { alert_date: "2026-09-02", relevance: "high", title: "Old" },
    { alert_date: "2026-09-03", relevance: "weak", title: "First" },
    { alert_date: "2026-09-09", relevance: "high", title: "Last" },
    { alert_date: "2026-09-10", relevance: "high", title: "Future" },
  ];
  assert.deepEqual(PaperFeed.selectWindow(records, start).map((x) => x.title), ["First", "Last"]);
});

test("calendar arithmetic crosses leap, month, and year boundaries in Shanghai", () => {
  assert.equal(PaperFeed.isoDate(PaperFeed.addDays(PaperFeed.dateFromIso("2024-02-28"), 1)), "2024-02-29");
  assert.equal(PaperFeed.isoDate(PaperFeed.addDays(PaperFeed.dateFromIso("2024-02-29"), 1)), "2024-03-01");
  assert.equal(PaperFeed.isoDate(PaperFeed.addDays(PaperFeed.dateFromIso("2025-12-31"), 1)), "2026-01-01");
});

test("malformed, impossible, and future starts fall back to the latest window", () => {
  for (const search of ["?start=nope", "?start=2026-02-30", "?start=2026-09-04", "?other=1"]) {
    assert.equal(PaperFeed.isoDate(PaperFeed.parseStart(search, today)), "2026-09-03");
  }
  assert.equal(PaperFeed.isoDate(PaperFeed.parseStart("?start=2026-09-03", today)), "2026-09-03");
});

test("sorting keeps date descending, relevance ascending, and equal titles stable", () => {
  const grouped = PaperFeed.sortAndGroup([
    { alert_date: "2026-09-05", relevance: "weak", title: "Zed" },
    { alert_date: "2026-09-05", relevance: "high", title: "Alpha", record_id: "first" },
    { alert_date: "2026-09-05", relevance: "high", title: "Alpha", record_id: "second" },
    { alert_date: "2026-09-05", relevance: "transferable", title: "Beta" },
    { alert_date: "2026-09-06", relevance: "weak", title: "Earlier group" },
  ]);
  assert.deepEqual(grouped.map((group) => group.date), ["2026-09-06", "2026-09-05"]);
  assert.deepEqual(grouped[1].papers.map((paper) => paper.record_id || paper.title), ["first", "second", "Beta", "Zed"]);
});

test("seven-day pager URLs preserve the selected range and stop after latest start", () => {
  const start = PaperFeed.dateFromIso("2026-08-27");
  assert.equal(PaperFeed.windowUrl("/paper-feed/", start), "/paper-feed/?start=2026-08-27");
  assert.equal(PaperFeed.isoDate(PaperFeed.addDays(start, 7)), "2026-09-03");
  assert.equal(PaperFeed.canGoNext(start, today), true);
  assert.equal(PaperFeed.canGoNext(PaperFeed.dateFromIso("2026-09-03"), today), false);
});

test("only HTTPS original links are accepted", () => {
  assert.equal(PaperFeed.safeExternalLink("https://example.org/paper"), "https://example.org/paper");
  assert.throws(() => PaperFeed.safeExternalLink("http://example.org/paper"), /unsafe paper URL/);
  assert.throws(() => PaperFeed.safeExternalLink("javascript:alert(1)"), /unsafe paper URL/);
});
