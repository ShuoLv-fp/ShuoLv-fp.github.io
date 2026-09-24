# Evidence-Driven Skills Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat bilingual Skills lists with an evidence-driven research profile, three future-direction cards, and a compact technical toolkit.

**Architecture:** Keep all English and Chinese content in their existing Jekyll include files, add one focused Sass partial for the component, and import that partial through the existing stylesheet entry point. The section remains static HTML/CSS with no JavaScript or new dependency, and structural tests protect bilingual parity and the evidence-first design.

**Tech Stack:** Jekyll, Kramdown, HTML, Sass/SCSS, Python `unittest`, existing light/dark theme selectors

## Global Constraints

- Keep the existing `#skills` anchor and homepage navigation destinations unchanged.
- Update English and Chinese pages with matching structures and equivalent content.
- Do not add percentage progress bars, numeric proficiency scores, JavaScript, dependencies, analytics, or backend services.
- Use textual status labels so meaning never depends on colour.
- Keep all content readable without hover and expose no hover-only information.
- Support light mode, dark mode, keyboard focus, reduced motion, print, and narrow mobile layouts without horizontal scrolling.
- Preserve all unrelated homepage sections.
- Use `#224B8D` as the evidence-blue accent, `#3F72B8` as signal blue, `#F4F7FB` as the quiet surface, `#253247` as light-mode ink, and `#D95D4F` only as the small exploration accent.

## File Map

- Modify `_pages/includes/technical_skills.md`: English section content and semantic component markup.
- Modify `_pages/includes/zh/technical_skills.md`: Chinese section content using the same class structure.
- Create `_sass/_skills.scss`: all Skills-profile layout, palette, interaction, dark-mode, reduced-motion, mobile, and print rules.
- Modify `assets/css/main.scss`: import the new Sass partial.
- Modify `tests/test_homepage_presentation.py`: structural, bilingual, content, and anti-regression tests.

---

### Task 1: Lock the bilingual evidence-first structure with failing tests

**Files:**
- Modify: `tests/test_homepage_presentation.py:65`
- Test: `tests/test_homepage_presentation.py`

**Interfaces:**
- Consumes: the two existing Markdown include paths.
- Produces: five structural expectations that the content and styling tasks must satisfy.

- [ ] **Step 1: Add focused tests before the `if __name__ == "__main__"` block**

```python
    def test_skills_sections_use_evidence_driven_structure(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn('class="skills-profile"', text)
                self.assertIn('class="skills-capabilities"', text)
                self.assertEqual(text.count('class="capability-card"'), 3)
                self.assertIn('class="exploration-grid"', text)
                self.assertEqual(text.count('class="exploration-card"'), 3)
                self.assertIn('class="technical-toolkit"', text)

    def test_skills_sections_connect_claims_to_evidence(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.count('class="evidence-row"'), 3)
                self.assertGreaterEqual(text.count('class="evidence-link"'), 6)
                self.assertIn('href="#publications"', text)
                self.assertIn('href="#projects"', text)

    def test_skills_sections_use_text_statuses_without_level_bars(self):
        for path in (
            Path("_pages/includes/technical_skills.md"),
            Path("_pages/includes/zh/technical_skills.md"),
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.count('class="capability-status"'), 6)
                self.assertNotIn("skill-bar", text)
                self.assertNotIn("aria-valuenow", text)

    def test_skills_content_is_localized(self):
        english = Path("_pages/includes/technical_skills.md").read_text(
            encoding="utf-8"
        )
        chinese = Path("_pages/includes/zh/technical_skills.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Demonstrated capabilities", english)
        self.assertIn("Computational Neuroscience &amp; Neuroimaging", english)
        self.assertIn("Exploring next", english)
        self.assertIn("Technical toolkit", english)

        self.assertIn("已验证的能力", chinese)
        self.assertIn("计算神经科学与神经影像", chinese)
        self.assertIn("正在探索", chinese)
        self.assertIn("技术工具箱", chinese)

    def test_skills_stylesheet_is_imported(self):
        entrypoint = Path("assets/css/main.scss").read_text(encoding="utf-8")
        partial = Path("_sass/_skills.scss")

        self.assertIn('@import "skills";', entrypoint)
        self.assertTrue(partial.is_file())
```

- [ ] **Step 2: Run the new tests and confirm they fail for the expected missing structure**

Run:

```bash
python -m unittest \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_use_evidence_driven_structure \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_connect_claims_to_evidence \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_use_text_statuses_without_level_bars \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_content_is_localized \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_stylesheet_is_imported -v
```

Expected: five failures caused by the absent `skills-profile` markup, missing Sass import, and missing `_sass/_skills.scss`.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_homepage_presentation.py
git commit -m "test: define evidence-driven skills structure"
```

---

### Task 2: Implement the English evidence-driven Skills content

**Files:**
- Modify: `_pages/includes/technical_skills.md:1-51`
- Test: `tests/test_homepage_presentation.py`

**Interfaces:**
- Consumes: existing homepage anchors `#publications` and `#projects` and the class names asserted by Task 1.
- Produces: English markup with exactly three `.capability-card` elements, three `.evidence-row` elements, six `.capability-status` elements, three `.exploration-card` elements, and one `.technical-toolkit`.

- [ ] **Step 1: Replace the English include with the approved content**

```html
<span class="anchor" id="skills"></span>
# 💻 Skills

<section class="skills-profile" aria-labelledby="skills-demonstrated-title">
  <p class="skills-intro">My skills are organized around two signals: capabilities demonstrated through published or shipped work, and directions I am actively developing for future research.</p>

  <div class="skills-section-heading">
    <span class="skills-kicker">Track record</span>
    <h2 id="skills-demonstrated-title">Demonstrated capabilities</h2>
  </div>

  <div class="skills-capabilities">
    <article class="capability-card">
      <header class="capability-header">
        <h3>Computational Neuroscience &amp; Neuroimaging</h3>
        <div class="capability-statuses" aria-label="Experience status">
          <span class="capability-status">Research-led</span>
          <span class="capability-status">Published</span>
        </div>
      </header>
      <p>I study how low-dimensional spatiotemporal dynamics and individualized network organization explain variation in brain function and behavior. My work combines fMRI, complex-valued decomposition, predictive modelling, and normative analysis.</p>
      <div class="evidence-row">
        <span class="evidence-label">Evidence</span>
        <span class="evidence-rail" aria-hidden="true"></span>
        <a class="evidence-link" href="#publications">Nature Communications · first author</a>
        <a class="evidence-link" href="#publications">Translational Psychiatry · accepted</a>
      </div>
      <div class="skill-keywords" aria-label="Methods">
        <span>fMRI</span><span>cPCA</span><span>sCCA</span><span>Normative Models</span><span>Network Neuroscience</span>
      </div>
    </article>

    <article class="capability-card">
      <header class="capability-header">
        <h3>LLM Agents &amp; Formal Reasoning</h3>
        <div class="capability-statuses" aria-label="Experience status">
          <span class="capability-status">Research-led</span>
          <span class="capability-status">Built</span>
        </div>
      </header>
      <p>I build agent systems that plan, solve, verify, and backtrack. At ByteDance Seed AI4Math, I developed test-time-scaling workflows for olympiad mathematics and a Lean 4 proof-quality pipeline combining static checks, retrieval, and LLM evaluation.</p>
      <div class="evidence-row">
        <span class="evidence-label">Evidence</span>
        <span class="evidence-rail" aria-hidden="true"></span>
        <a class="evidence-link" href="#projects">Seed AI4Math · research internship</a>
        <a class="evidence-link" href="#projects">Lean 4 proof QA · 600+ items</a>
      </div>
      <div class="skill-keywords" aria-label="Methods">
        <span>Multi-Agent Systems</span><span>Test-Time Scaling</span><span>Lean 4</span><span>Verification</span><span>LLM Evaluation</span>
      </div>
    </article>

    <article class="capability-card">
      <header class="capability-header">
        <h3>Complex Systems &amp; Intelligent Applications</h3>
        <div class="capability-statuses" aria-label="Experience status">
          <span class="capability-status">Published</span>
          <span class="capability-status">Built</span>
        </div>
      </header>
      <p>I translate mathematical models into working intelligent systems, from epidemic-awareness dynamics on complex networks to uncertainty-aware multimodal recognition and personalized AIGC applications.</p>
      <div class="evidence-row">
        <span class="evidence-label">Evidence</span>
        <span class="evidence-rail" aria-hidden="true"></span>
        <a class="evidence-link" href="#publications">Nonlinear Dynamics · first author</a>
        <a class="evidence-link" href="#projects">National award-winning systems</a>
      </div>
      <div class="skill-keywords" aria-label="Methods">
        <span>Complex Networks</span><span>Dynamical Systems</span><span>Multimodal Learning</span><span>Three-Way Decisions</span><span>AIGC</span>
      </div>
    </article>
  </div>

  <div class="skills-section-heading skills-exploration-heading">
    <span class="skills-kicker skills-kicker--exploring">Research horizon</span>
    <h2>Exploring next</h2>
    <p>Directions where I am building depth and looking for research collaboration.</p>
  </div>

  <div class="exploration-grid">
    <article class="exploration-card">
      <h3>Brain-inspired foundation models</h3>
      <p>Connecting neural representations, multimodal foundation models, and computational accounts of cognition.</p>
      <div class="skill-keywords"><span>Neural Representation</span><span>Multimodal Models</span><span>Cognition</span></div>
    </article>
    <article class="exploration-card">
      <h3>Autonomous agents for science</h3>
      <p>Building agents that can plan experiments, use tools, verify reasoning, and advance scientific workflows.</p>
      <div class="skill-keywords"><span>Scientific Agents</span><span>Tool Use</span><span>Self-Verification</span></div>
    </article>
    <article class="exploration-card">
      <h3>Trustworthy human–AI collaboration</h3>
      <p>Designing auditable and controllable agent systems with explicit evidence, risk boundaries, and human oversight.</p>
      <div class="skill-keywords"><span>Human-in-the-Loop</span><span>Auditability</span><span>AI Safety</span></div>
    </article>
  </div>

  <div class="technical-toolkit" aria-labelledby="technical-toolkit-title">
    <div class="skills-section-heading skills-toolkit-heading">
      <span class="skills-kicker">Working stack</span>
      <h2 id="technical-toolkit-title">Technical toolkit</h2>
    </div>
    <dl class="toolkit-list">
      <div><dt>Programming</dt><dd><a href="https://www.python.org/">Python</a><span>C++</span><span>Java</span><span>R</span><a href="https://lean-lang.org/">Lean</a><span>HTML</span></dd></div>
      <div><dt>Machine learning</dt><dd><a href="https://pytorch.org/">PyTorch</a><span>scikit-learn</span><span>Hugging Face</span><span>NumPy / SciPy</span><span>Pandas</span><span>PyTorch Geometric</span></dd></div>
      <div><dt>Agents &amp; language models</dt><dd><span>LangChain</span><span>LangGraph</span><span>LlamaIndex</span><span>vLLM</span><span>Ollama</span><span>MCP</span><span>Multi-Agent Orchestration</span><span>Test-Time Scaling</span></dd></div>
      <div><dt>Neuroimaging &amp; research</dt><dd><span>fMRIPrep</span><span>Nilearn</span><span>FSL</span><span>PLINK</span><span>LaTeX</span><span>Git</span></dd></div>
    </dl>
  </div>
</section>
```

- [ ] **Step 2: Run the English-facing test subset**

Run:

```bash
python -m unittest \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_use_evidence_driven_structure \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_connect_claims_to_evidence \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_use_text_statuses_without_level_bars \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_content_is_localized -v
```

Expected: failures remain for the Chinese file, while English subtest failures disappear.

- [ ] **Step 3: Commit the English content**

```bash
git add _pages/includes/technical_skills.md
git commit -m "feat: add evidence-driven English skills profile"
```

---

### Task 3: Implement the matching Chinese Skills content

**Files:**
- Modify: `_pages/includes/zh/technical_skills.md:1-51`
- Test: `tests/test_homepage_presentation.py`

**Interfaces:**
- Consumes: the English component structure and class contract from Task 2.
- Produces: equivalent Chinese content with identical card, status, evidence, exploration, and toolkit counts.

- [ ] **Step 1: Replace the Chinese include with localized content using the same markup contract**

Use the same element hierarchy and classes from Task 2. Translate the visible strings as follows while keeping product names, venue names, and technical terms in their established forms:

```html
<span class="anchor" id="skills"></span>
# 💻 技能

<section class="skills-profile" aria-labelledby="skills-demonstrated-title-zh">
  <p class="skills-intro">我的技能按两类信号组织：由论文或落地成果验证的能力，以及我正在持续积累、希望在未来研究中深入发展的方向。</p>

  <div class="skills-section-heading">
    <span class="skills-kicker">研究履历</span>
    <h2 id="skills-demonstrated-title-zh">已验证的能力</h2>
  </div>

  <div class="skills-capabilities">
    <article class="capability-card">
      <header class="capability-header"><h3>计算神经科学与神经影像</h3><div class="capability-statuses" aria-label="经验状态"><span class="capability-status">研究主导</span><span class="capability-status">论文验证</span></div></header>
      <p>我关注低维时空动力学和个体化网络组织如何解释脑功能与行为差异，并综合运用 fMRI、复值分解、预测建模与规范模型开展研究。</p>
      <div class="evidence-row"><span class="evidence-label">成果证据</span><span class="evidence-rail" aria-hidden="true"></span><a class="evidence-link" href="#publications">Nature Communications · 第一作者</a><a class="evidence-link" href="#publications">Translational Psychiatry · 已接收</a></div>
      <div class="skill-keywords" aria-label="研究方法"><span>fMRI</span><span>cPCA</span><span>sCCA</span><span>规范模型</span><span>网络神经科学</span></div>
    </article>

    <article class="capability-card">
      <header class="capability-header"><h3>大语言模型智能体与形式化推理</h3><div class="capability-statuses" aria-label="经验状态"><span class="capability-status">研究主导</span><span class="capability-status">系统落地</span></div></header>
      <p>我构建能够规划、求解、验证和回溯的智能体系统。在字节跳动 Seed AI4Math 实习期间，我开发了面向奥数推理的测试时扩展流程，以及结合静态检查、检索与大模型评估的 Lean 4 证明质量管线。</p>
      <div class="evidence-row"><span class="evidence-label">成果证据</span><span class="evidence-rail" aria-hidden="true"></span><a class="evidence-link" href="#projects">Seed AI4Math · 研究实习</a><a class="evidence-link" href="#projects">Lean 4 证明质检 · 600+ 条</a></div>
      <div class="skill-keywords" aria-label="研究方法"><span>多智能体系统</span><span>测试时扩展</span><span>Lean 4</span><span>形式化验证</span><span>大模型评估</span></div>
    </article>

    <article class="capability-card">
      <header class="capability-header"><h3>复杂系统建模与智能应用</h3><div class="capability-statuses" aria-label="经验状态"><span class="capability-status">论文验证</span><span class="capability-status">系统落地</span></div></header>
      <p>我将数学模型转化为可运行的智能系统，研究覆盖复杂网络上的疫情—意识耦合动力学、不确定性感知的多模态识别，以及个性化 AIGC 应用。</p>
      <div class="evidence-row"><span class="evidence-label">成果证据</span><span class="evidence-rail" aria-hidden="true"></span><a class="evidence-link" href="#publications">Nonlinear Dynamics · 第一作者</a><a class="evidence-link" href="#projects">国家级获奖智能系统</a></div>
      <div class="skill-keywords" aria-label="研究方法"><span>复杂网络</span><span>动力系统</span><span>多模态学习</span><span>三支决策</span><span>AIGC</span></div>
    </article>
  </div>

  <div class="skills-section-heading skills-exploration-heading"><span class="skills-kicker skills-kicker--exploring">研究视野</span><h2>正在探索</h2><p>我正在建立研究积累，也期待开展合作的方向。</p></div>
  <div class="exploration-grid">
    <article class="exploration-card"><h3>类脑基础模型</h3><p>连接神经表征、多模态基础模型与认知过程的计算解释。</p><div class="skill-keywords"><span>神经表征</span><span>多模态模型</span><span>认知建模</span></div></article>
    <article class="exploration-card"><h3>面向科学发现的自主智能体</h3><p>构建能够规划实验、调用工具、验证推理并推进科研流程的智能体。</p><div class="skill-keywords"><span>科学智能体</span><span>工具调用</span><span>自我验证</span></div></article>
    <article class="exploration-card"><h3>可信的人机协作</h3><p>设计具有显式证据、风险边界和人类监督机制的可审计、可控制智能体系统。</p><div class="skill-keywords"><span>人在回路</span><span>可审计性</span><span>AI 安全</span></div></article>
  </div>

  <div class="technical-toolkit" aria-labelledby="technical-toolkit-title-zh">
    <div class="skills-section-heading skills-toolkit-heading"><span class="skills-kicker">工作栈</span><h2 id="technical-toolkit-title-zh">技术工具箱</h2></div>
    <dl class="toolkit-list">
      <div><dt>编程语言</dt><dd><a href="https://www.python.org/">Python</a><span>C++</span><span>Java</span><span>R</span><a href="https://lean-lang.org/">Lean</a><span>HTML</span></dd></div>
      <div><dt>机器学习</dt><dd><a href="https://pytorch.org/">PyTorch</a><span>scikit-learn</span><span>Hugging Face</span><span>NumPy / SciPy</span><span>Pandas</span><span>PyTorch Geometric</span></dd></div>
      <div><dt>智能体与大语言模型</dt><dd><span>LangChain</span><span>LangGraph</span><span>LlamaIndex</span><span>vLLM</span><span>Ollama</span><span>MCP</span><span>多智能体编排</span><span>测试时扩展</span></dd></div>
      <div><dt>神经影像与科研</dt><dd><span>fMRIPrep</span><span>Nilearn</span><span>FSL</span><span>PLINK</span><span>LaTeX</span><span>Git</span></dd></div>
    </dl>
  </div>
</section>
```

- [ ] **Step 2: Run all content-structure tests**

Run:

```bash
python -m unittest \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_use_evidence_driven_structure \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_connect_claims_to_evidence \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_sections_use_text_statuses_without_level_bars \
  tests.test_homepage_presentation.HomepagePresentationTests.test_skills_content_is_localized -v
```

Expected: four tests pass. The stylesheet-import test remains failing until Task 4.

- [ ] **Step 3: Commit the Chinese content**

```bash
git add _pages/includes/zh/technical_skills.md
git commit -m "feat: add evidence-driven Chinese skills profile"
```

---

### Task 4: Add the component styling and accessibility states

**Files:**
- Create: `_sass/_skills.scss`
- Modify: `assets/css/main.scss:34`
- Test: `tests/test_homepage_presentation.py`

**Interfaces:**
- Consumes: every class introduced by Tasks 2 and 3.
- Produces: responsive visual hierarchy, the evidence-rail signature, theme variants, focus states, reduced-motion behaviour, and print fallbacks.

- [ ] **Step 1: Create `_sass/_skills.scss` with scoped component rules**

```scss
/* Evidence-driven Skills profile */
.skills-profile {
  --skills-blue: #224b8d;
  --skills-signal: #3f72b8;
  --skills-mist: #f4f7fb;
  --skills-ink: #253247;
  --skills-coral: #d95d4f;
  --skills-border: #dce4ef;
  color: var(--skills-ink);
}

.skills-intro {
  max-width: 62rem;
  margin: 0 0 1.75rem;
  color: #536176;
  font-size: 1.02em;
  line-height: 1.7;
}

.skills-section-heading {
  margin: 1.75rem 0 0.9rem;
}

.skills-section-heading h2 {
  margin: 0.15rem 0 0;
  color: var(--skills-ink);
  font-size: 1.34em;
  line-height: 1.25;
}

.skills-section-heading p {
  margin: 0.4rem 0 0;
  color: #667389;
}

.skills-kicker {
  color: var(--skills-blue);
  font-size: 0.7em;
  font-weight: 800;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

.skills-kicker--exploring {
  color: var(--skills-coral);
}

.skills-capabilities {
  display: grid;
  gap: 1rem;
}

.capability-card,
.exploration-card,
.technical-toolkit {
  border: 1px solid var(--skills-border);
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(34, 75, 141, 0.06);
}

.capability-card {
  padding: 1.25rem 1.4rem 1.15rem;
  border-radius: 10px;
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.capability-card:hover {
  border-color: rgba(63, 114, 184, 0.55);
  box-shadow: 0 12px 28px rgba(34, 75, 141, 0.11);
  transform: translateY(-2px);
}

.capability-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.capability-header h3,
.exploration-card h3 {
  margin: 0;
  color: var(--skills-ink);
  line-height: 1.32;
}

.capability-header h3 {
  font-size: 1.12em;
}

.capability-card > p {
  margin: 0.75rem 0 0.9rem;
  line-height: 1.65;
}

.capability-statuses {
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.35rem;
}

.capability-status {
  padding: 0.22rem 0.62rem;
  border: 1px solid rgba(34, 75, 141, 0.22);
  border-radius: 999px;
  background: rgba(34, 75, 141, 0.08);
  color: var(--skills-blue);
  font-size: 0.72em;
  font-weight: 750;
  line-height: 1.3;
  white-space: nowrap;
}

.evidence-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0.85rem 0 0.7rem;
}

.evidence-label {
  color: var(--skills-blue);
  font-size: 0.72em;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.evidence-rail {
  width: clamp(1.5rem, 5vw, 4.2rem);
  height: 2px;
  background: linear-gradient(90deg, var(--skills-signal), rgba(63, 114, 184, 0.18));
}

.evidence-link {
  padding: 0.2rem 0.62rem;
  border: 1px solid rgba(34, 75, 141, 0.18);
  border-radius: 999px;
  background: var(--skills-mist);
  color: var(--skills-blue);
  font-size: 0.76em;
  font-weight: 650;
  text-decoration: none;
}

.evidence-link:hover {
  border-color: var(--skills-signal);
  text-decoration: none;
}

.evidence-link:focus-visible,
.technical-toolkit a:focus-visible {
  outline: 3px solid rgba(63, 114, 184, 0.36);
  outline-offset: 3px;
}

.skill-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.skill-keywords span {
  padding: 0.14rem 0.5rem;
  border-radius: 4px;
  background: #f1f3f6;
  color: #596578;
  font-family: Monaco, Consolas, "Lucida Console", monospace;
  font-size: 0.68em;
  line-height: 1.45;
}

.skills-exploration-heading {
  margin-top: 2.2rem;
}

.exploration-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
}

.exploration-card {
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 1.05rem 1rem 0.95rem;
  overflow: hidden;
  border-radius: 8px;
  background: linear-gradient(145deg, #ffffff, #fafbfd);
}

.exploration-card::before {
  position: absolute;
  top: 0;
  left: 0;
  width: 2.6rem;
  height: 3px;
  background: var(--skills-coral);
  content: "";
}

.exploration-card h3 {
  font-size: 0.98em;
}

.exploration-card p {
  margin: 0.6rem 0 0.9rem;
  color: #657287;
  font-size: 0.9em;
  line-height: 1.58;
}

.exploration-card .skill-keywords {
  margin-top: auto;
}

.technical-toolkit {
  margin-top: 2.2rem;
  padding: 1.15rem 1.3rem 0.8rem;
  border-radius: 10px;
  background: var(--skills-mist);
  box-shadow: none;
}

.skills-toolkit-heading {
  margin: 0 0 0.8rem;
}

.toolkit-list,
.toolkit-list > div,
.toolkit-list dt,
.toolkit-list dd {
  margin: 0;
}

.toolkit-list > div {
  display: grid;
  grid-template-columns: minmax(9.5rem, 0.26fr) 1fr;
  gap: 0.85rem;
  padding: 0.72rem 0;
  border-top: 1px solid rgba(34, 75, 141, 0.12);
}

.toolkit-list dt {
  color: var(--skills-ink);
  font-weight: 750;
}

.toolkit-list dd {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem 0.75rem;
}

.toolkit-list dd span,
.toolkit-list dd a {
  color: #56647a;
  font-size: 0.88em;
  text-decoration: none;
}

.toolkit-list dd span::before,
.toolkit-list dd a::before {
  color: var(--skills-signal);
  content: "·";
  margin-right: 0.32rem;
}

[data-theme="dark"] .skills-profile {
  --skills-mist: #252b33;
  --skills-ink: #eef3fb;
  --skills-border: #3b4553;
  color: #d8dee8;
}

[data-theme="dark"] .skills-intro,
[data-theme="dark"] .skills-section-heading p,
[data-theme="dark"] .exploration-card p {
  color: #b7c0ce;
}

[data-theme="dark"] .capability-card,
[data-theme="dark"] .exploration-card {
  background: #242a31;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.22);
}

[data-theme="dark"] .exploration-card {
  background: linear-gradient(145deg, #242a31, #20252c);
}

[data-theme="dark"] .capability-status,
[data-theme="dark"] .evidence-link {
  border-color: rgba(110, 168, 254, 0.32);
  background: rgba(110, 168, 254, 0.1);
  color: #9fc3ff;
}

[data-theme="dark"] .skills-kicker,
[data-theme="dark"] .evidence-label {
  color: #9fc3ff;
}

[data-theme="dark"] .skill-keywords span {
  background: #303741;
  color: #c4ccd7;
}

[data-theme="dark"] .technical-toolkit {
  background: #242a31;
}

[data-theme="dark"] .toolkit-list > div {
  border-top-color: rgba(159, 195, 255, 0.16);
}

[data-theme="dark"] .toolkit-list dd span,
[data-theme="dark"] .toolkit-list dd a {
  color: #c4ccd7;
}

@media (max-width: 760px) {
  .capability-header {
    flex-direction: column;
    gap: 0.65rem;
  }

  .capability-statuses {
    justify-content: flex-start;
  }

  .exploration-grid {
    grid-template-columns: 1fr;
  }

  .toolkit-list > div {
    grid-template-columns: 1fr;
    gap: 0.35rem;
  }
}

@media (max-width: 420px) {
  .capability-card,
  .technical-toolkit {
    padding-right: 1rem;
    padding-left: 1rem;
  }

  .evidence-rail {
    display: none;
  }

  .evidence-link {
    max-width: 100%;
    white-space: normal;
  }
}

@media (prefers-reduced-motion: reduce) {
  .capability-card {
    transition: none;
  }

  .capability-card:hover {
    transform: none;
  }
}

@media print {
  .capability-card,
  .exploration-card,
  .technical-toolkit {
    break-inside: avoid;
    border-color: #aeb7c4;
    background: #ffffff;
    box-shadow: none;
  }

  .evidence-link {
    border: 0;
    padding: 0;
    background: transparent;
  }
}
```

- [ ] **Step 2: Import the partial from `assets/css/main.scss` immediately after `@import "paper-feed";`**

```scss
@import "paper-feed";
@import "skills";
```

- [ ] **Step 3: Run the stylesheet contract test and the full presentation test module**

Run:

```bash
python -m unittest tests.test_homepage_presentation -v
```

Expected: all tests in `tests.test_homepage_presentation` pass.

- [ ] **Step 4: Compile the site to catch Sass, Liquid, and Kramdown errors**

Run:

```bash
bundle exec jekyll build
```

Expected: exit code 0 and a successful build of `_site/index.html` and `_site/zh/index.html` with no Sass or Liquid errors.

- [ ] **Step 5: Commit the component styling**

```bash
git add _sass/_skills.scss assets/css/main.scss
git commit -m "style: add responsive skills profile design"
```

---

### Task 5: Verify rendered output and guard the final integration

**Files:**
- Modify only if verification exposes a defect: `_pages/includes/technical_skills.md`, `_pages/includes/zh/technical_skills.md`, or `_sass/_skills.scss`
- Test: `tests/test_homepage_presentation.py`

**Interfaces:**
- Consumes: the complete bilingual component and compiled stylesheet.
- Produces: verified desktop/mobile, light/dark, keyboard, reduced-motion, and print behaviour with no unrelated regression.

- [ ] **Step 1: Run the repository test suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: all discovered tests pass. If an unrelated environment-dependent test is unavailable, record its exact output and still run `tests.test_homepage_presentation` separately to verify this feature.

- [ ] **Step 2: Start the local Jekyll preview**

Run:

```bash
bundle exec jekyll serve --host 127.0.0.1 --port 4000
```

Expected: the server reports `Server address: http://127.0.0.1:4000/` and remains running for browser inspection.

- [ ] **Step 3: Inspect both rendered routes at desktop and mobile widths**

Open `http://127.0.0.1:4000/#skills` and `http://127.0.0.1:4000/zh/#skills`. At approximately 1440 px and 390 px viewport widths, confirm:

- three demonstrated-capability cards appear in a readable vertical stack;
- each claim is visually connected to evidence chips by the evidence rail on desktop;
- three exploration cards form one row on desktop and one column on mobile;
- toolkit rows wrap without horizontal overflow;
- status labels never cover titles;
- light and dark themes preserve readable borders, text, chips, and focus rings;
- keyboard Tab navigation reaches every evidence and toolkit link with a visible focus indicator;
- reduced-motion mode removes card movement;
- print preview removes shadows and keeps cards together where possible.

- [ ] **Step 4: Validate generated semantic structure**

Run:

```bash
rg -n 'skills-profile|capability-card|exploration-card|technical-toolkit' \
  _site/index.html _site/zh/index.html
```

Expected: both generated pages contain the component root, three capability cards, three exploration cards, and one toolkit.

- [ ] **Step 5: Run final whitespace and change-scope checks**

Run:

```bash
git diff --check
git status --short
git diff --stat HEAD~4..HEAD
```

Expected: no whitespace errors; only the two Skills includes, one Sass partial, the Sass entry point, tests, and this plan/spec documentation are involved in the feature.

- [ ] **Step 6: Commit any verification fixes, only if Step 3 exposed a defect**

```bash
git add _pages/includes/technical_skills.md \
  _pages/includes/zh/technical_skills.md \
  _sass/_skills.scss
git commit -m "fix: refine skills profile presentation"
```

If no files changed during verification, do not create an empty commit.
