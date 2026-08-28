import { SELF, reset } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";

const origin = "https://agent.test";

async function authenticatedCookie() {
  const response = await SELF.fetch(`${origin}/api/login`, {
    method: "POST",
    headers: { "content-type": "application/json", origin },
    body: JSON.stringify({ password: "synthetic-test-password" })
  });
  return response.headers.get("set-cookie").split(";", 1)[0];
}

async function uiSources() {
  const cookie = await authenticatedCookie();
  const [login, loginJs, html, appJs] = await Promise.all([
    SELF.fetch(`${origin}/`).then((response) => response.text()),
    SELF.fetch(`${origin}/login.js`).then((response) => response.text()),
    SELF.fetch(`${origin}/app`, { headers: { cookie } }).then((response) => response.text()),
    SELF.fetch(`${origin}/app.js`, { headers: { cookie } }).then((response) => response.text())
  ]);
  return { login, loginJs, html, appJs };
}

describe("private dossier UI", () => {
  beforeEach(async () => {
    await reset();
  });

  it("has login, sync, export and logout controls without send controls", async () => {
    const { login, html, appJs } = await uiSources();
    expect(login).toContain('id="workflow-password"');
    expect(login).toContain('autocomplete="current-password"');
    expect(html).toContain('id="sync-cloud"');
    expect(html).toContain('id="export-backup"');
    expect(html).toContain('id="logout"');
    expect(appJs).toContain("409");
    expect(appJs).toContain("unsynchronized");
    expect(`${login}\n${html}\n${appJs}`).not.toMatch(/send email|smtp|mailto:/i);
  });

  it("keeps secrets and workflow records out of persistent browser storage", async () => {
    const { loginJs, appJs } = await uiSources();
    expect(loginJs).toContain('passwordInput.value = ""');
    expect(`${loginJs}\n${appJs}`).not.toMatch(/localStorage|sessionStorage|indexedDB/i);
    expect(appJs).toContain('fetch("/api/bootstrap"');
    expect(appJs).toContain("dirtyRecords: new Map()");
  });

  it("does not serve legacy JSON data paths", async () => {
    for (const path of ["profile", "faculty", "programs", "applications", "artifacts"]) {
      expect((await SELF.fetch(`${origin}/data/${path}.json`)).status).toBe(404);
    }
  });
});
