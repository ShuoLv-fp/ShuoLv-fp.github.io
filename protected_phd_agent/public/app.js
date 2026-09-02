const state = {
  authenticated: false,
  csrf: "",
  revision: 0,
  profile: {},
  faculty: [],
  programs: [],
  applications: [],
  artifacts: [],
  dirtyRecords: new Map(),
  activeDossierId: null,
  activeView: "dossiers",
  syncState: "clean",
  advisorFilter: ""
};

const viewTitles = {
  dashboard: "Application overview",
  dossiers: "Advisor dossiers",
  drafts: "Draft desk",
  profile: "Applicant profile"
};

function element(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value === null || value === undefined) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = String(value);
    else if (key === "onclick") node.addEventListener("click", value);
    else if (key === "oninput") node.addEventListener("input", value);
    else if (key === "onchange") node.addEventListener("change", value);
    else if (typeof value === "boolean") node.toggleAttribute(key, value);
    else node.setAttribute(key, String(value));
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child instanceof Node) node.appendChild(child);
    else if (child !== null && child !== undefined) node.appendChild(document.createTextNode(String(child)));
  }
  return node;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function safeExternalUrl(value) {
  try {
    const url = new URL(value);
    return new Set(["https:", "http:"]).has(url.protocol) ? url.href : "#";
  } catch {
    return "#";
  }
}

function safeLogoPath(value) {
  return typeof value === "string" && /^\/logos\/[a-z0-9_-]+\.svg$/i.test(value)
    ? value
    : "/logos/institution.svg";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    credentials: "same-origin",
    headers: {
      ...(options.body ? { "content-type": "application/json" } : {}),
      ...(options.method && options.method !== "GET" ? { "x-csrf-token": state.csrf } : {}),
      ...(options.headers || {})
    }
  });

  if (response.status === 401) {
    state.authenticated = false;
    showRelogin("Your session expired. Unlock the workspace to preserve unsynchronized edits.");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(payload.error || `Request failed (${response.status})`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return response;
}

async function login(password) {
  const response = await fetch("/api/login", {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ password })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(response.status === 429
      ? "Too many attempts. Wait fifteen minutes before trying again."
      : payload.error || "The password was not accepted.");
    error.status = response.status;
    throw error;
  }
  state.authenticated = true;
  state.csrf = payload.csrf;
  return payload;
}

async function session() {
  const response = await fetch("/api/session", { credentials: "same-origin" });
  if (!response.ok) {
    window.location.replace("/");
    return false;
  }
  const payload = await response.json();
  state.authenticated = true;
  state.csrf = payload.csrf;
  return true;
}

async function bootstrap() {
  const response = await fetch("/api/bootstrap", { credentials: "same-origin" });
  if (response.status === 401) {
    window.location.replace("/");
    return false;
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || "The private workflow has not been imported yet.");
  }
  const data = await response.json();
  state.revision = Number(data.revision || 0);
  state.profile = data.profile || {};
  state.faculty = Array.isArray(data.faculty) ? data.faculty : [];
  state.programs = Array.isArray(data.programs) ? data.programs : [];
  state.applications = Array.isArray(data.applications) ? data.applications : [];
  state.artifacts = Array.isArray(data.artifacts) ? data.artifacts : [];
  const dossiers = dossierRows();
  if (!dossiers.some((row) => row.id === state.activeDossierId)) {
    state.activeDossierId = dossiers[0]?.id || null;
  }
  return true;
}

function markDirty(collection, id, patch) {
  const key = `${collection}:${id}`;
  state.dirtyRecords.set(key, {
    collection,
    id,
    patch: { ...(state.dirtyRecords.get(key)?.patch || {}), ...patch }
  });
  setSyncState("unsynchronized");
}

function mergeRecord(collection, record) {
  const index = state[collection].findIndex((item) => item.id === record.id);
  if (index >= 0) state[collection][index] = record;
}

async function syncCloud() {
  if (!state.dirtyRecords.size) {
    setSyncState("clean");
    return;
  }
  setSyncState("syncing");
  document.getElementById("conflict-panel").hidden = true;

  for (const [key, change] of [...state.dirtyRecords]) {
    try {
      const response = await api(`/api/${change.collection}/${encodeURIComponent(change.id)}`, {
        method: "PUT",
        body: JSON.stringify({ expectedRevision: state.revision, patch: change.patch })
      });
      const payload = await response.json();
      state.revision = payload.revision;
      mergeRecord(change.collection, payload.record);
      state.dirtyRecords.delete(key);
    } catch (error) {
      if (error.status === 409) {
        setSyncState("conflict");
        document.getElementById("conflict-panel").hidden = false;
        return;
      }
      setSyncState("error", error.message);
      return;
    }
  }

  setSyncState("clean");
  renderCurrentView();
}

async function exportBackup() {
  try {
    const response = await api("/api/export");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = element("a", { href: url, download: `phd-agent-backup-r${state.revision}.json` });
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    setSyncState("error", error.message);
  }
}

async function logout() {
  if (state.dirtyRecords.size && !window.confirm("Lock the workspace and discard unsynchronized changes?")) return;
  try {
    await api("/api/logout", { method: "POST", body: "{}" });
  } finally {
    state.csrf = "";
    state.profile = {};
    state.faculty = [];
    state.programs = [];
    state.applications = [];
    state.artifacts = [];
    state.dirtyRecords.clear();
    window.location.replace("/");
  }
}

function setSyncState(next, detail = "") {
  state.syncState = next;
  const indicator = document.getElementById("sync-indicator");
  const button = document.getElementById("sync-cloud");
  const labels = {
    clean: `Cloud saved · r${state.revision}`,
    unsynchronized: `${state.dirtyRecords.size} unsynchronized change${state.dirtyRecords.size === 1 ? "" : "s"}`,
    syncing: "Syncing…",
    conflict: "Revision conflict",
    error: detail || "Sync failed"
  };
  indicator.textContent = labels[next] || next;
  indicator.dataset.state = next;
  button.disabled = next === "clean" || next === "syncing";
}

function dossierRows() {
  return state.faculty
    .filter((row) => Number(row.featured_rank) > 0)
    .sort((left, right) => Number(left.featured_rank) - Number(right.featured_rank));
}

function linkedDraft(facultyId) {
  return state.artifacts.find((item) => item.kind === "outreach_email" && item.target_id === facultyId);
}

function renderDashboard() {
  const metrics = document.getElementById("overview-metrics");
  clear(metrics);
  const dossiers = dossierRows();
  const reviewed = state.artifacts.filter((item) => item.status === "reviewed").length;
  const shortlisted = dossiers.filter((item) => item.status === "shortlisted").length;
  const values = [
    [dossiers.length, "Curated advisors"],
    [state.artifacts.length, "Outreach drafts"],
    [reviewed, "Reviewed drafts"],
    [shortlisted, "Shortlisted"]
  ];
  for (const [value, label] of values) {
    metrics.appendChild(element("article", { class: "metric" }, [
      element("strong", { text: value }),
      element("span", { text: label })
    ]));
  }

  const focus = document.getElementById("overview-focus");
  clear(focus);
  const top = dossiers.slice(0, 5);
  focus.appendChild(element("div", { class: "focus-heading" }, [
    element("p", { class: "signal-label", text: "CURATED PRIORITY" }),
    element("h3", { text: "First research conversations" })
  ]));
  const list = element("ol", { class: "focus-list" });
  for (const advisor of top) {
    list.appendChild(element("li", {}, [
      element("button", {
        class: "focus-link",
        text: `${advisor.display_name || advisor.name} @ ${advisor.institution_short || advisor.institution}`,
        onclick: () => openDossier(advisor.id)
      }),
      element("span", { text: advisor.research_area || "Research fit brief" })
    ]));
  }
  focus.appendChild(list);
}

function renderDossiers() {
  const rows = dossierRows().filter((row) => {
    const haystack = `${row.display_name || row.name} ${row.institution_short || ""} ${row.institution || ""}`.toLowerCase();
    return haystack.includes(state.advisorFilter.toLowerCase());
  });
  document.getElementById("dossier-count").textContent = `${dossierRows().length} advisors`;
  const nav = document.getElementById("dossier-nav");
  clear(nav);
  if (!rows.length) {
    nav.appendChild(element("p", { class: "empty-note", text: "No advisor matches this filter." }));
  }
  for (const row of rows) {
    const label = row.display_name || row.name || "Advisor";
    const institution = row.institution_short || row.institution || "Institution";
    nav.appendChild(element("button", {
      class: `advisor-tab${row.id === state.activeDossierId ? " active" : ""}`,
      title: `Open ${label} dossier`,
      onclick: () => {
        state.activeDossierId = row.id;
        renderDossiers();
      }
    }, [
      element("img", { src: safeLogoPath(row.institution_mark), alt: "" }),
      element("span", { class: "advisor-tab-copy" }, [
        element("strong", { text: label }),
        element("small", { text: `@ ${institution}` })
      ]),
      element("span", {
        class: "fit-chip",
        text: row.fit && Number.isFinite(Number(row.fit.total)) ? row.fit.total : "—"
      })
    ]));
  }

  const active = dossierRows().find((row) => row.id === state.activeDossierId);
  renderDossierDetail(active);
}

function renderDossierDetail(row) {
  const detail = document.getElementById("dossier-detail");
  clear(detail);
  if (!row) {
    detail.appendChild(element("div", { class: "empty-state" }, [
      element("p", { class: "signal-label", text: "NO DOSSIER" }),
      element("h2", { text: "Import the private workflow to begin." })
    ]));
    return;
  }

  const name = row.display_name || row.name;
  const institution = row.institution_short || row.institution;
  const analysis = row.match_analysis || {};
  const draft = linkedDraft(row.id);
  const officialUrl = safeExternalUrl(row.homepage_url);
  const hero = element("header", { class: "dossier-hero" }, [
    element("div", { class: "advisor-identity" }, [
      element("img", { class: "hero-mark", src: safeLogoPath(row.institution_mark), alt: "" }),
      element("div", {}, [
        element("p", {
          class: "utility-label",
          text: `DOSSIER ${String(row.featured_rank || "—").padStart(2, "0")} · ${(row.entry_type || "FACULTY").toUpperCase()}`
        }),
        element("h2", { text: `${name} @ ${institution}` }),
        element("p", { class: "advisor-meta", text: row.institution || institution })
      ])
    ]),
    element("div", { class: "hero-actions" }, [
      element("span", {
        class: "fit-signal",
        text: row.fit?.total !== undefined ? `${row.fit.total}/100 fit signal` : "Qualitative fit"
      }),
      officialUrl === "#"
        ? null
        : element("a", { class: "external-link", href: officialUrl, target: "_blank", rel: "noreferrer", text: "Official profile ↗" })
    ])
  ]);
  detail.appendChild(hero);

  if (row.source_correction) {
    detail.appendChild(element("aside", { class: "source-alert" }, [
      element("strong", { text: "Source check" }),
      element("span", { text: "The original list required identity verification; this dossier uses the corrected research profile." })
    ]));
  }

  const research = element("section", { class: "research-section" }, [
    element("div", { class: "section-marker", text: "RESEARCH MAP" }),
    element("div", { class: "section-copy" }, [
      element("h3", { text: "Research direction" }),
      element("p", { class: "lead-copy", text: row.research_summary || "Research summary pending review." })
    ])
  ]);
  if (Array.isArray(row.keywords) && row.keywords.length) {
    research.querySelector(".section-copy").appendChild(element("div", { class: "keyword-line" },
      row.keywords.slice(0, 9).map((keyword) => element("span", { text: keyword }))
    ));
  }
  detail.appendChild(research);

  detail.appendChild(element("section", { class: "research-section" }, [
    element("div", { class: "section-marker", text: "FIT MEMO" }),
    element("div", { class: "section-copy" }, [
      element("h3", { text: "Why the work could connect" }),
      element("p", { class: "lead-copy", text: analysis.summary || "Fit synthesis pending review." }),
      element("div", { class: "evidence-grid" }, [
        memo("Profile evidence", analysis.alignment_points),
        memo("Conversation angles", analysis.conversation_angles, "accent")
      ]),
      element("div", { class: "caution-strip" }, [
        element("strong", { text: "Before contact" }),
        element("span", { text: analysis.caution || "Verify current projects and supervision availability." })
      ])
    ])
  ]));

  detail.appendChild(renderNotes(row));
  detail.appendChild(renderEmailWorkbench(row, draft));
}

function memo(title, points = [], modifier = "") {
  const card = element("div", { class: `memo ${modifier}`.trim() }, [element("strong", { text: title })]);
  const list = element("ul");
  for (const point of Array.isArray(points) ? points : []) list.appendChild(element("li", { text: point }));
  if (!list.children.length) list.appendChild(element("li", { text: "Add evidence after reviewing the profile." }));
  card.appendChild(list);
  return card;
}

function renderNotes(row) {
  const notes = element("textarea", {
    id: "advisor-notes",
    spellcheck: "true",
    placeholder: "Private notes for your next review"
  });
  notes.value = row.notes || "";
  notes.addEventListener("input", () => markDirty("faculty", row.id, { notes: notes.value }));

  const status = element("select", { id: "advisor-status" }, [
    element("option", { value: "discovered", text: "Discovered" }),
    element("option", { value: "shortlisted", text: "Shortlisted" }),
    element("option", { value: "contacted", text: "Contacted" })
  ]);
  status.value = row.status || "discovered";
  status.addEventListener("change", () => markDirty("faculty", row.id, { status: status.value }));

  return element("section", { class: "research-section compact" }, [
    element("div", { class: "section-marker", text: "YOUR NOTES" }),
    element("div", { class: "section-copy notes-grid" }, [
      element("label", {}, [element("span", { text: "Review status" }), status]),
      element("label", {}, [element("span", { text: "Private notes" }), notes])
    ])
  ]);
}

function renderEmailWorkbench(row, draft) {
  const section = element("section", { class: "email-workbench" }, [
    element("div", { class: "email-title" }, [
      element("div", {}, [
        element("p", { class: "utility-label", text: "TAILORED OUTREACH" }),
        element("h3", { text: "Editable draft" })
      ]),
      element("span", { class: "review-flag", text: "DRAFT · REVIEW REQUIRED" })
    ])
  ]);
  if (!draft) {
    section.appendChild(element("p", { class: "empty-note", text: "No draft is linked to this advisor." }));
    return section;
  }

  const contactEmail = element("input", {
    id: "advisor-contact-email",
    type: "email",
    readonly: true,
    value: row.contact_email || "Email not published"
  });
  const contactActions = element("div", { class: "contact-email-actions" }, [
    contactEmail,
    element("button", {
      class: "button secondary",
      type: "button",
      text: "Copy email",
      disabled: !row.contact_email,
      onclick: async () => {
        await navigator.clipboard.writeText(row.contact_email);
      }
    }),
    row.contact_email_source_url
      ? element("a", {
        class: "contact-source",
        href: safeExternalUrl(row.contact_email_source_url),
        target: "_blank",
        rel: "noopener noreferrer",
        text: "Official source ↗"
      })
      : null
  ]);
  const subject = element("input", { id: "advisor-email-subject", type: "text" });
  subject.value = draft.subject || "";
  const content = element("textarea", { id: "advisor-email-editor", spellcheck: "true" });
  content.value = draft.content || "";
  const updateDraft = () => markDirty("artifacts", draft.id, {
    subject: subject.value,
    content: content.value,
    status: "draft",
    requires_human_review: true
  });
  subject.addEventListener("input", updateDraft);
  content.addEventListener("input", updateDraft);

  section.append(
    element("label", { class: "editor-field" }, [element("span", { text: "Contact email" }), contactActions]),
    element("label", { class: "editor-field" }, [element("span", { text: "Subject" }), subject]),
    element("label", { class: "editor-field" }, [element("span", { text: "Body" }), content]),
    element("div", { class: "editor-actions" }, [
      element("button", { class: "button primary", type: "button", text: "Sync this draft", onclick: syncCloud }),
      element("button", {
        class: "button secondary",
        type: "button",
        text: "Copy draft",
        onclick: async () => {
          await navigator.clipboard.writeText(content.value);
          setSyncState(state.dirtyRecords.size ? "unsynchronized" : "clean");
        }
      }),
      element("span", { class: "editor-note", text: "No transmission action exists in this workspace." })
    ])
  );
  return section;
}

function renderDrafts() {
  const container = document.getElementById("draft-list");
  clear(container);
  for (const draft of state.artifacts) {
    const advisor = state.faculty.find((item) => item.id === draft.target_id);
    container.appendChild(element("article", { class: "draft-row" }, [
      element("div", {}, [
        element("p", { class: "utility-label", text: draft.status || "draft" }),
        element("h3", { text: draft.subject || "Untitled outreach draft" }),
        element("p", { text: advisor ? `${advisor.display_name || advisor.name} @ ${advisor.institution_short || advisor.institution}` : draft.target_name || "Unlinked advisor" })
      ]),
      advisor
        ? element("button", { class: "button secondary", type: "button", text: "Open dossier", onclick: () => openDossier(advisor.id) })
        : null
    ]));
  }
  if (!container.children.length) container.appendChild(element("p", { class: "empty-note", text: "No outreach drafts are available." }));
}

function renderProfile() {
  const container = document.getElementById("profile-content");
  clear(container);
  const profile = state.profile || {};
  const identity = profile.identity || {};
  container.appendChild(element("header", { class: "profile-hero" }, [
    element("p", { class: "utility-label", text: profile.cycle || "APPLICATION PROFILE" }),
    element("h2", { text: identity.name || "Applicant profile" }),
    element("p", { text: profile.vision || "Research vision pending review." })
  ]));
  const grid = element("div", { class: "profile-grid" });
  grid.append(
    profileList("Research priorities", profile.research_priorities),
    profileList("Education", (profile.education || []).map((item) => `${item.degree || ""} · ${item.institution || ""}`)),
    profileList("Selected projects", (profile.projects || []).map((item) => item.title || item.name || "Project")),
    profileList("Skills", Array.isArray(profile.skills) ? profile.skills : Object.values(profile.skills || {}).flat())
  );
  container.appendChild(grid);
}

function profileList(title, items = []) {
  const card = element("section", { class: "profile-card" }, [element("h3", { text: title })]);
  const list = element("ul");
  for (const item of Array.isArray(items) ? items : []) {
    const text = typeof item === "string" ? item : item?.name || item?.title || JSON.stringify(item);
    if (text) list.appendChild(element("li", { text }));
  }
  if (!list.children.length) list.appendChild(element("li", { text: "No entries yet." }));
  card.appendChild(list);
  return card;
}

function openDossier(id) {
  state.activeDossierId = id;
  window.location.hash = "dossiers";
  route();
}

function route() {
  const requested = window.location.hash.replace("#", "");
  state.activeView = viewTitles[requested] ? requested : "dossiers";
  for (const view of document.querySelectorAll("[data-view]")) {
    view.hidden = view.dataset.view !== state.activeView;
  }
  for (const link of document.querySelectorAll("[data-view-link]")) {
    link.classList.toggle("active", link.dataset.viewLink === state.activeView);
  }
  document.getElementById("page-title").textContent = viewTitles[state.activeView];
  renderCurrentView();
}

function renderCurrentView() {
  if (state.activeView === "dashboard") renderDashboard();
  else if (state.activeView === "drafts") renderDrafts();
  else if (state.activeView === "profile") renderProfile();
  else renderDossiers();
}

function showRelogin(message) {
  const dialog = document.getElementById("relogin-dialog");
  document.getElementById("relogin-error").textContent = message;
  if (!dialog.open) dialog.showModal();
  document.getElementById("relogin-password").focus();
}

async function refreshCloud() {
  if (state.dirtyRecords.size && !window.confirm("Refresh and discard unsynchronized edits in this browser?")) return;
  state.dirtyRecords.clear();
  await bootstrap();
  document.getElementById("conflict-panel").hidden = true;
  setSyncState("clean");
  renderCurrentView();
}

function bindEvents() {
  window.addEventListener("hashchange", route);
  document.getElementById("sync-cloud").addEventListener("click", syncCloud);
  document.getElementById("export-backup").addEventListener("click", exportBackup);
  document.getElementById("conflict-export").addEventListener("click", exportBackup);
  document.getElementById("refresh-cloud").addEventListener("click", refreshCloud);
  document.getElementById("logout").addEventListener("click", logout);
  document.getElementById("advisor-search").addEventListener("input", (event) => {
    state.advisorFilter = event.target.value;
    renderDossiers();
  });
  document.getElementById("relogin-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("relogin-password");
    const password = input.value;
    input.value = "";
    try {
      await login(password);
      document.getElementById("relogin-dialog").close();
      document.getElementById("relogin-error").textContent = "";
      setSyncState(state.dirtyRecords.size ? "unsynchronized" : "clean");
    } catch (error) {
      document.getElementById("relogin-error").textContent = error.message;
      input.focus();
    }
  });
}

async function boot() {
  bindEvents();
  if (!(await session())) return;
  try {
    await bootstrap();
    setSyncState("clean");
    route();
  } catch (error) {
    setSyncState("error", error.message);
    const detail = document.getElementById("dossier-detail");
    clear(detail);
    detail.appendChild(element("div", { class: "empty-state" }, [
      element("p", { class: "signal-label", text: "WORKFLOW UNAVAILABLE" }),
      element("h2", { text: error.message })
    ]));
  }
}

boot();
