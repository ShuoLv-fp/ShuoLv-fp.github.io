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

describe("private research briefings", () => {
  beforeEach(async () => {
    await reset();
  });

  it("keeps the briefing document, styles and figures behind authentication", async () => {
    const paths = [
      "/research/ewu-ultralow-field-mri.html",
      "/research/ewu-ultralow-field-mri.css",
      "/research/ewu-ultralow-field-mri/whole-body-system.jpg"
    ];
    for (const path of paths) {
      expect((await SELF.fetch(`${origin}${path}`)).status).toBe(401);
    }

    const cookie = await authenticatedCookie();
    for (const path of paths) {
      const response = await SELF.fetch(`${origin}${path}`, { headers: { cookie } });
      if (response.status === 404) return;
      expect(response.status).toBe(200);
    }
  });

  it("adds a dedicated research briefing view to the authenticated workspace", async () => {
    const cookie = await authenticatedCookie();
    const [html, appJs] = await Promise.all([
      SELF.fetch(`${origin}/app`, { headers: { cookie } }).then((response) => response.text()),
      SELF.fetch(`${origin}/app.js`, { headers: { cookie } }).then((response) => response.text())
    ]);

    expect(html).toContain('data-view-link="research"');
    expect(html).toContain('id="view-research"');
    expect(html).toContain('id="research-briefing"');
    expect(appJs).toContain('research: "Research briefings"');
    expect(appJs).toContain('api("/research/ewu-ultralow-field-mri.html"');
    expect(appJs).toContain("bindResearchFilters");
  });

  it("serves the complete personalized Wu Lab research map", async () => {
    const cookie = await authenticatedCookie();
    const response = await SELF.fetch(`${origin}/research/ewu-ultralow-field-mri.html`, {
      headers: { cookie }
    });
    if (response.status === 404) return;
    const briefing = await response.text();

    expect(briefing.match(/<article class="paper-card"/g)).toHaveLength(18);
    expect(briefing.match(/<figure class="evidence-figure"/g)).toHaveLength(6);
    expect(briefing).toContain("人脑动力学与个体差异");
    expect(briefing).toContain("BrainLMM 与基础模型");
    expect(briefing).toContain("规范模型与临床泛化");
    expect(briefing).toContain("AI Agent 与科研工作流");
    expect(briefing).toContain("研究推演，不是吴老师团队的既有结论");
  });
});
