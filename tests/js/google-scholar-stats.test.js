"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function page(language = "en") {
  const elements = Object.fromEntries(["total_cit", "h_index"]
    .map(id => [id, { textContent: "--", title: "" }]));
  const requests = [];
  const document = {
    documentElement: { lang: language },
    getElementById: id => elements[id],
    getElementsByClassName: () => [],
  };
  const $ = () => ({ ready: callback => callback() });
  $.ajax = options => { requests.push(options); };
  // Support the old loader so the regression fails on freshness, not its API.
  $.getJSON = (url, success) => {
    const request = { url, success };
    requests.push(request);
    return { fail: callback => { request.error = callback; } };
  };
  const source = fs.readFileSync("_includes/fetch_google_scholar_stats.html", "utf8")
    .replaceAll("<script>", "").replaceAll("</script>", "")
    .replace(/{%[\s\S]*?%}/g, "")
    .replace(/{{\s*site.repository\s*}}/g, "owner/repository");
  vm.runInNewContext(source, { $, document, Date, console });
  return { requests, elements };
}

const recent = { citedby: 42, hindex: 3, updated: "2026-11-14T01:17:00+00:00" };
const old = { citedby: 28, hindex: 2, updated: "2026-09-08 03:07:39.339949" };

test("both sources are checked and older CDN data never replaces newer raw data", () => {
  const { requests, elements } = page();
  assert.equal(requests.length, 2);
  const raw = requests.find(request => request.url.includes("raw.githubusercontent"));
  const cdn = requests.find(request => request.url.includes("jsdelivr"));
  raw.success(recent);
  cdn.success(old);
  assert.equal(elements.total_cit.textContent, "42");
  assert.equal(elements.h_index.textContent, "3");
  assert.equal(elements.scholar_updated, undefined);
});

test("newer raw data replaces an already rendered cached response", () => {
  const { requests, elements } = page();
  assert.equal(requests.length, 2);
  requests[1].success(old);
  requests[0].success(recent);
  assert.equal(elements.total_cit.textContent, "42");
});

test("a failed source leaves the valid metrics visible without an update date", () => {
  const { requests, elements } = page("zh");
  assert.equal(requests.length, 2);
  requests[1].success(old);
  requests[0].error();
  assert.equal(elements.total_cit.textContent, "28");
  assert.equal(elements.scholar_updated, undefined);
});

test("malformed or failed responses never render invalid metrics", () => {
  for (const payload of [null, {}, { ...recent, citedby: -1 }, { ...recent, hindex: "3" }, { ...recent, updated: "invalid" }]) {
    const { requests, elements } = page();
    assert.equal(requests.length, 2);
    requests[0].success(payload);
    requests[1].error();
    assert.equal(elements.total_cit.textContent, "--");
    assert.equal(elements.h_index.textContent, "--");
  }
});

test("legitimate zero metrics render and requests bypass cache with bounded timeouts", () => {
  const { requests, elements } = page();
  assert.equal(requests.length, 2);
  requests[0].success({ ...recent, citedby: 0, hindex: 0 });
  assert.equal(elements.total_cit.textContent, "0");
  for (const request of requests) {
    assert.equal(request.cache, false);
    assert.ok(request.timeout > 0 && request.timeout <= 15000);
  }
});
