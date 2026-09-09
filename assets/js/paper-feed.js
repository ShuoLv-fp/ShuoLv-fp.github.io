(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.PaperFeed = api;
}(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  var DAY_MS = 24 * 60 * 60 * 1000;
  var relevanceRank = { high: 0, transferable: 1, weak: 2 };
  var copy = {
    en: {
      loading: "Loading papers…", error: "The paper feed could not be loaded. Please try again later.", empty: "No papers were selected for this seven-day window.",
      unavailable: "Summary unavailable.", evidence: "Evidence", original: "Original paper", previous: "Previous 7 days", next: "Next 7 days", latest: "Latest",
      high: "High relevance", transferable: "Transferable", weak: "Background", conclusion: "Core conclusion", points: "Key points", connection: "Research connection", tags: "Topics",
      abstract: "Public abstract", snippet: "Email snippet", metadata: "Metadata only", unavailableEvidence: "Unavailable", range: "Reading window"
    },
    zh: {
      loading: "正在加载论文…", error: "论文速递暂时无法加载，请稍后再试。", empty: "这个七天窗口暂无入选论文。",
      unavailable: "摘要暂不可用。", evidence: "证据", original: "查看原文", previous: "前 7 天", next: "后 7 天", latest: "最新",
      high: "高度相关", transferable: "可迁移", weak: "背景参考", conclusion: "核心结论", points: "关键要点", connection: "研究关联", tags: "主题",
      abstract: "公开摘要", snippet: "邮件片段", metadata: "仅元数据", unavailableEvidence: "不可用", range: "阅读区间"
    }
  };

  function dateFromIso(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    var parts = value.split("-").map(Number);
    var date = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
    return isoDate(date) === value ? date : null;
  }

  function isoDate(date) {
    return date.getUTCFullYear() + "-" + String(date.getUTCMonth() + 1).padStart(2, "0") + "-" + String(date.getUTCDate()).padStart(2, "0");
  }

  function shanghaiToday(date) {
    var parts = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date);
    var values = {};
    parts.forEach(function (part) { values[part.type] = part.value; });
    return new Date(Date.UTC(Number(values.year), Number(values.month) - 1, Number(values.day)));
  }

  function addDays(date, count) { return new Date(date.getTime() + count * DAY_MS); }
  function latestStart(today) { return addDays(shanghaiToday(today || new Date()), -6); }

  function parseStart(search, today) {
    var fallback = latestStart(today);
    var input = new URLSearchParams(search || "").get("start");
    var start = dateFromIso(input);
    return start && start.getTime() <= fallback.getTime() ? start : fallback;
  }

  function selectWindow(records, start) {
    var low = isoDate(start);
    var high = isoDate(addDays(start, 7));
    return (Array.isArray(records) ? records : []).filter(function (record) {
      return record && typeof record.alert_date === "string" && record.alert_date >= low && record.alert_date < high;
    });
  }

  function sortAndGroup(records) {
    var indexed = (Array.isArray(records) ? records : []).map(function (paper, index) { return { paper: paper, index: index }; });
    indexed.sort(function (left, right) {
      var a = left.paper, b = right.paper;
      var byDate = String(b.alert_date).localeCompare(String(a.alert_date));
      if (byDate) return byDate;
      var aRank = Object.prototype.hasOwnProperty.call(relevanceRank, a.relevance) ? relevanceRank[a.relevance] : 99;
      var bRank = Object.prototype.hasOwnProperty.call(relevanceRank, b.relevance) ? relevanceRank[b.relevance] : 99;
      var byRelevance = aRank - bRank;
      if (byRelevance) return byRelevance;
      var byIngested = String(b.ingested_at || "").localeCompare(String(a.ingested_at || ""));
      if (byIngested) return byIngested;
      var byTitle = String(a.title || "").localeCompare(String(b.title || ""));
      return byTitle || left.index - right.index;
    });
    return indexed.reduce(function (groups, entry) {
      var date = entry.paper.alert_date;
      var previous = groups[groups.length - 1];
      if (!previous || previous.date !== date) groups.push({ date: date, papers: [] });
      groups[groups.length - 1].papers.push(entry.paper);
      return groups;
    }, []);
  }

  function windowUrl(pathname, start) { return pathname + "?start=" + encodeURIComponent(isoDate(start)); }
  function canGoNext(start, today) { return addDays(start, 7).getTime() <= latestStart(today).getTime(); }
  function isLatest(start, today) { return start.getTime() === latestStart(today).getTime(); }
  function safeExternalLink(url) {
    var parsed;
    try { parsed = new URL(url); } catch (_) { throw new Error("unsafe paper URL"); }
    if (parsed.protocol !== "https:") throw new Error("unsafe paper URL");
    return parsed.href;
  }

  function element(document, tag, className, value) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined && value !== null) node.textContent = String(value);
    return node;
  }

  function localizedDate(date, lang) {
    var safeDate = dateFromIso(date);
    return safeDate ? new Intl.DateTimeFormat(lang === "zh" ? "zh-CN" : "en-US", { timeZone: "UTC", year: "numeric", month: "long", day: "numeric", weekday: "long" }).format(safeDate) : date;
  }

  function localizedRange(start, lang, labels) {
    return labels.range + " · " + localizedDate(isoDate(start), lang) + " — " + localizedDate(isoDate(addDays(start, 6)), lang);
  }

  function appendSummary(document, card, paper, lang, labels) {
    if (paper.status === "summary_unavailable" || !paper[lang]) {
      card.appendChild(element(document, "p", "paper-feed-card__unavailable", labels.unavailable));
      return;
    }
    var summary = paper[lang];
    if (summary.core_conclusion) {
      card.appendChild(element(document, "h4", "paper-feed-card__label", labels.conclusion));
      card.appendChild(element(document, "p", "paper-feed-card__conclusion", summary.core_conclusion));
    }
    if (Array.isArray(summary.key_points) && summary.key_points.length) {
      card.appendChild(element(document, "h4", "paper-feed-card__label", labels.points));
      var points = element(document, "ul", "paper-feed-card__points");
      summary.key_points.forEach(function (point) { points.appendChild(element(document, "li", "", point)); });
      card.appendChild(points);
    }
    if (summary.research_connection) {
      card.appendChild(element(document, "h4", "paper-feed-card__label", labels.connection));
      card.appendChild(element(document, "p", "paper-feed-card__connection", summary.research_connection));
    }
    if (Array.isArray(summary.tags) && summary.tags.length) {
      var tags = element(document, "p", "paper-feed-card__tags");
      tags.appendChild(element(document, "span", "paper-feed-card__label", labels.tags + ": "));
      tags.appendChild(element(document, "span", "", summary.tags.join(" · ")));
      card.appendChild(tags);
    }
  }

  function appendPaper(document, container, paper, lang, labels) {
    var relevance = Object.prototype.hasOwnProperty.call(relevanceRank, paper.relevance) ? paper.relevance : "weak";
    var card = element(document, "article", "paper-feed-card paper-feed-card--" + relevance);
    var heading = element(document, "h3", "paper-feed-card__title", paper.title || "");
    card.appendChild(heading);
    var meta = [Array.isArray(paper.authors) ? paper.authors.join(", ") : "", paper.venue || "", paper.year || ""].filter(Boolean).join(" · ");
    if (meta) card.appendChild(element(document, "p", "paper-feed-card__meta", meta));
    card.appendChild(element(document, "span", "paper-feed-card__badge paper-feed-card__badge--" + relevance, labels[relevance] || labels.weak));
    appendSummary(document, card, paper, lang, labels);
    var source = element(document, "p", "paper-feed-card__source");
    var evidence = paper.evidence_type === "unavailable" ? labels.unavailableEvidence : labels[paper.evidence_type] || labels.unavailableEvidence;
    source.appendChild(element(document, "span", "", labels.evidence + ": " + evidence));
    try {
      var link = element(document, "a", "paper-feed-card__original", labels.original);
      link.href = safeExternalLink(paper.canonical_url);
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      source.appendChild(document.createTextNode(" · "));
      source.appendChild(link);
    } catch (_) { /* A missing or unsafe URL is intentionally not rendered. */ }
    card.appendChild(source);
    container.appendChild(card);
  }

  function renderPager(document, container, lang, start, today) {
    var labels = copy[lang] || copy.en;
    var pager = element(document, "nav", "paper-feed__pager");
    pager.setAttribute("aria-label", lang === "zh" ? "论文窗口导航" : "Paper window navigation");
    [
      [addDays(start, -7), labels.previous, false],
      [addDays(start, 7), labels.next, !canGoNext(start, today)],
      [latestStart(today), labels.latest, isLatest(start, today)]
    ].forEach(function (entry) {
      var button = element(document, "button", "paper-feed__pager-button", entry[1]);
      button.type = "button";
      button.disabled = entry[2];
      if (!entry[2]) button.addEventListener("click", function () { window.location.assign(windowUrl(window.location.pathname, entry[0])); });
      pager.appendChild(button);
    });
    container.replaceChildren(pager);
  }

  function render(root, payload, lang, search, today) {
    var document = root.ownerDocument;
    var labels = copy[lang] || copy.en;
    var start = parseStart(search, today);
    var status = root.querySelector("[data-paper-feed-status]");
    var range = root.querySelector("[data-paper-feed-range]");
    var days = root.querySelector("[data-paper-feed-days]");
    var pagers = root.querySelectorAll("[data-paper-feed-pager]");
    pagers.forEach(function (pager) { renderPager(document, pager, lang, start, today); });
    if (range) range.textContent = localizedRange(start, lang, labels);
    days.replaceChildren();
    if (!payload || payload.schema_version !== 1 || !Array.isArray(payload.papers)) {
      status.textContent = labels.error;
      return;
    }
    var groups = sortAndGroup(selectWindow(payload.papers, start));
    if (!groups.length) { status.textContent = labels.empty; return; }
    status.textContent = "";
    groups.forEach(function (group) {
      var day = element(document, "section", "paper-feed__day");
      day.appendChild(element(document, "h2", "paper-feed__date", localizedDate(group.date, lang)));
      group.papers.forEach(function (paper) { appendPaper(document, day, paper, lang, labels); });
      days.appendChild(day);
    });
  }

  function boot() {
    var root = document.querySelector("[data-paper-feed]");
    if (!root) return;
    var alternate = document.querySelector("[data-paper-feed-alternate]");
    if (alternate) alternate.href = alternate.href.split("?")[0] + window.location.search;
    var lang = root.getAttribute("data-lang") === "zh" ? "zh" : "en";
    var status = root.querySelector("[data-paper-feed-status]");
    status.textContent = (copy[lang] || copy.en).loading;
    fetch(root.getAttribute("data-feed-url"), { credentials: "same-origin" })
      .then(function (response) { if (!response.ok) throw new Error("feed request failed"); return response.json(); })
      .then(function (payload) { render(root, payload, lang, window.location.search, new Date()); })
      .catch(function () { status.textContent = (copy[lang] || copy.en).error; });
  }

  if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded", boot);

  return { addDays: addDays, canGoNext: canGoNext, dateFromIso: dateFromIso, isLatest: isLatest, isoDate: isoDate, parseStart: parseStart, safeExternalLink: safeExternalLink, selectWindow: selectWindow, sortAndGroup: sortAndGroup, windowUrl: windowUrl, render: render };
}));
