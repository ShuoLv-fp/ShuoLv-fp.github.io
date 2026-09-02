# CV Sidebar and Recent Projects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish both September 2026 CVs in the bilingual profile sidebar and replace Recent Projects with seven CV-backed, synchronized English and Chinese entries.

**Architecture:** Keep the existing Jekyll configuration/template/include structure. Add two language-specific CV properties to the author configuration, render them in both desktop and compact profile controls, and keep project copy in the existing bilingual Markdown includes. A source-level regression suite locks down assets, labels, accessibility, project ordering, verified metrics, removed claims, and timestamps.

**Tech Stack:** Jekyll 3.9, Liquid, Kramdown GFM, Python `unittest`, static PDF assets

## Global Constraints

- Treat `/Users/shuolv/Desktop/Code/Secmind/output/pdf/Shuo_Lv_Academic_CV_Template.pdf` and `/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.pdf` as the sources of truth.
- Copy the English PDF to `assets/files/CV202609_EN.pdf` and the Chinese PDF to `assets/files/CV202609_ZH.pdf` without modifying their bytes.
- Preserve the existing homepage layout, native disclosure interaction, typography, colors, and unrelated profile links.
- Keep English and Chinese project facts, order, dates, metrics, and outcomes synchronized.
- Do not touch unrelated work in `protected_phd_agent/` or change the GitHub Pages hosting architecture.

---

### Task 1: Add CV and project regression coverage

**Files:**
- Create: `tests/test_cv_projects_update.py`

**Interfaces:**
- Consumes: `_config.yml`, `_includes/author-profile.html`, the two Recent Projects includes, the two homepage files, and `assets/files/`.
- Produces: `CvProjectsUpdateTests`, the acceptance suite for Tasks 2 and 3.

- [ ] **Step 1: Write the failing regression test**

```python
from pathlib import Path
import re
import unittest


class CvProjectsUpdateTests(unittest.TestCase):
    def test_bilingual_cv_assets_and_configuration(self):
        config = Path("_config.yml").read_text(encoding="utf-8")
        self.assertRegex(
            config,
            r'(?m)^  cv_en\s+: "assets/files/CV202609_EN\.pdf"$',
        )
        self.assertRegex(
            config,
            r'(?m)^  cv_zh\s+: "assets/files/CV202609_ZH\.pdf"$',
        )
        self.assertNotRegex(config, r"(?m)^  cv\s+:")
        for path in (
            Path("assets/files/CV202609_EN.pdf"),
            Path("assets/files/CV202609_ZH.pdf"),
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)

    def test_sidebar_exposes_both_localized_cv_links(self):
        profile = Path("_includes/author-profile.html").read_text(
            encoding="utf-8"
        )
        for label in (
            "CV (English, Sep 2026)",
            "CV (Chinese, Sep 2026)",
            "英文简历（2026 年 9 月）",
            "中文简历（2026 年 9 月）",
        ):
            with self.subTest(label=label):
                self.assertIn(label, profile)
        for key, label_key in (("cv_en", "t_cv_en"), ("cv_zh", "t_cv_zh")):
            with self.subTest(key=key):
                self.assertEqual(2, profile.count(f"{{% if author.{key} %}}"))
                self.assertEqual(
                    2,
                    profile.count(
                        f'href="{{{{ site.baseurl }}}}/{{{{ author.{key} }}}}"'
                    ),
                )
                self.assertIn(f'aria-label="{{{{ {label_key} }}}}"', profile)

    def test_recent_projects_match_cv_scope_and_order(self):
        expected = {
            Path("_pages/includes/recent_projects.md"): [
                "General-Purpose Cybersecurity Agent",
                "ByteDance Seed AI4Math Research Internship",
                "Low-Dimensional Spatiotemporal Dynamics of the Human Brain",
                "Complex Social Awareness Modeling",
                "Intelligent Factory Security",
                "Large Language Model for Early Childhood Education",
                "Xiangqi Game-Playing System",
            ],
            Path("_pages/includes/zh/recent_projects.md"): [
                "通用网安智能体",
                "字节跳动 Seed AI4Math 研究实习",
                "低维人脑时空动态",
                "复杂社会意识建模",
                "工厂智慧安防",
                "幼教大模型",
                "中国象棋博弈系统",
            ],
        }
        for path, titles in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                headings = re.findall(r"(?m)^\*\*(.+?)\*\*", text)
                self.assertEqual(7, len(headings))
                positions = [text.index(f"**{title}**") for title in titles]
                self.assertEqual(sorted(positions), positions)

    def test_recent_projects_include_verified_metrics_only(self):
        english = Path("_pages/includes/recent_projects.md").read_text(
            encoding="utf-8"
        )
        chinese = Path("_pages/includes/zh/recent_projects.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "5 specialized agents",
            "16-node bounded state machine",
            "R0-R3",
            "Finding-Evidence",
            "5 iterations",
            "100+ problems",
            "6.4/7",
            "600+ formalized data items",
            "70%+",
            "2,000+ data items",
            "11 production and quality specifications",
        ):
            with self.subTest(language="en", phrase=phrase):
                self.assertIn(phrase, english)
        for phrase in (
            "5 类专业 Agent",
            "16 节点有界状态机",
            "R0-R3",
            "Finding-Evidence",
            "5 个版本",
            "100 题以上",
            "6.4/7",
            "600+ 条形式化数据",
            "70%+",
            "2,000+ 条数据",
            "11 份数据生产与质量规范",
        ):
            with self.subTest(language="zh", phrase=phrase):
                self.assertIn(phrase, chinese)
        for obsolete in (
            "Development of LLM-Driven Smart Cultural Tourism System",
            "Leadership Evaluation Framework Under Polygenic Risk",
            "7-role",
            "thousands of agent actions",
        ):
            self.assertNotIn(obsolete, english)
        for obsolete in (
            "大模型驱动的智慧文旅系统",
            "多基因风险下的领导力评估框架",
            "7 角色",
            "上千次智能体动作",
        ):
            self.assertNotIn(obsolete, chinese)

    def test_homepage_timestamps_are_september_2026(self):
        self.assertIn(
            "Last updated: Sep. 2026",
            Path("_pages/about.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "最后更新：2026 年 9 月",
            Path("_pages/zh.md").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python3 -m unittest tests/test_cv_projects_update.py -v`

Expected: FAIL because the September CV assets/configuration, dual sidebar links, seven-project content, and September timestamps do not exist yet.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_cv_projects_update.py
git commit -m "test: cover bilingual CV and project updates"
```

### Task 2: Publish both CV downloads in the sidebar

**Files:**
- Create: `assets/files/CV202609_EN.pdf`
- Create: `assets/files/CV202609_ZH.pdf`
- Modify: `_config.yml:41`
- Modify: `_includes/author-profile.html:5-27`
- Modify: `_includes/author-profile.html:55-57`
- Modify: `_includes/author-profile.html:156-158`
- Test: `tests/test_cv_projects_update.py`

**Interfaces:**
- Consumes: the two source PDFs and Jekyll's `site.author` configuration.
- Produces: `author.cv_en`, `author.cv_zh`, `t_cv_en`, and `t_cv_zh`, rendered in desktop and mobile profile controls.

- [ ] **Step 1: Copy the source PDFs without transforming them**

```bash
cp '/Users/shuolv/Desktop/Code/Secmind/output/pdf/Shuo_Lv_Academic_CV_Template.pdf' assets/files/CV202609_EN.pdf
cp '/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.pdf' assets/files/CV202609_ZH.pdf
cmp -s '/Users/shuolv/Desktop/Code/Secmind/output/pdf/Shuo_Lv_Academic_CV_Template.pdf' assets/files/CV202609_EN.pdf
cmp -s '/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.pdf' assets/files/CV202609_ZH.pdf
```

Expected: both comparison commands exit 0.

- [ ] **Step 2: Replace the single CV configuration property**

Replace `_config.yml`'s `cv` line with:

```yaml
  cv_en            : "assets/files/CV202609_EN.pdf"
  cv_zh            : "assets/files/CV202609_ZH.pdf"
```

- [ ] **Step 3: Define localized labels in the profile template**

Use these assignments in the existing language branches:

```liquid
{% if page.lang == 'zh' %}
  {% assign t_cv_en = '英文简历（2026 年 9 月）' %}
  {% assign t_cv_zh = '中文简历（2026 年 9 月）' %}
{% else %}
  {% assign t_cv_en = 'CV (English, Sep 2026)' %}
  {% assign t_cv_zh = 'CV (Chinese, Sep 2026)' %}
{% endif %}
```

Keep the existing non-CV label assignments inside their current branches.

- [ ] **Step 4: Render both desktop links**

Replace the single desktop CV block with:

```liquid
      {% if author.cv_en %}
        <li><a href="{{ site.baseurl }}/{{ author.cv_en }}"><i class="fas fa-fw fa-file-pdf" aria-hidden="true"></i> {{ t_cv_en }}</a></li>
      {% endif %}
      {% if author.cv_zh %}
        <li><a href="{{ site.baseurl }}/{{ author.cv_zh }}"><i class="fas fa-fw fa-file-pdf" aria-hidden="true"></i> {{ t_cv_zh }}</a></li>
      {% endif %}
```

- [ ] **Step 5: Render accessible compact links**

Replace the single compact CV block with:

```liquid
      {% if author.cv_en %}
        <a href="{{ site.baseurl }}/{{ author.cv_en }}" aria-label="{{ t_cv_en }}" title="{{ t_cv_en }}"><i class="fas fa-fw fa-file-pdf" aria-hidden="true"></i></a>
      {% endif %}
      {% if author.cv_zh %}
        <a href="{{ site.baseurl }}/{{ author.cv_zh }}" aria-label="{{ t_cv_zh }}" title="{{ t_cv_zh }}"><i class="fas fa-fw fa-file-pdf" aria-hidden="true"></i></a>
      {% endif %}
```

- [ ] **Step 6: Run the sidebar regression tests**

Run: `python3 -m unittest tests.test_cv_projects_update.CvProjectsUpdateTests.test_bilingual_cv_assets_and_configuration tests.test_cv_projects_update.CvProjectsUpdateTests.test_sidebar_exposes_both_localized_cv_links -v`

Expected: both tests PASS.

- [ ] **Step 7: Commit the CV asset and sidebar update**

```bash
git add assets/files/CV202609_EN.pdf assets/files/CV202609_ZH.pdf _config.yml _includes/author-profile.html
git commit -m "feat: add bilingual September 2026 CV links"
```

### Task 3: Align Recent Projects with the September 2026 CVs

**Files:**
- Modify: `_pages/includes/recent_projects.md`
- Modify: `_pages/includes/zh/recent_projects.md`
- Modify: `_pages/about.md:59`
- Modify: `_pages/zh.md:56`
- Test: `tests/test_cv_projects_update.py`

**Interfaces:**
- Consumes: the verified facts and metrics in the supplied CVs.
- Produces: seven ordered English project headings and seven fact-equivalent Chinese project headings inside the existing disclosure panel.

- [ ] **Step 1: Replace the English Recent Projects include**

Use this complete content:

```markdown
<span class='anchor' id='projects'></span>
<details markdown="1">
<summary style="cursor: pointer; font-size: 1.25em; margin-bottom: 8px;">🚀 <strong>Recent Projects</strong> <span style="font-weight: normal; opacity: .7;">(7 projects — click to expand)</span></summary>

**General-Purpose Cybersecurity Agent** (SWU, Jun. 2026-Present)

- **Role:** Project Lead; **Advisor:** Prof. Libo Zhang
- Built 5 specialized agents and a 16-node bounded state machine with LangGraph for code audit, penetration testing, incident response, and reverse engineering. The architecture separates LLM-based interpretation, planning, and reflection from explicit permissions, routing, and termination rules.
- Designed R0-R3 risk levels, Finding-Evidence validation, human approval for high-risk actions, and a two-layer state/domain blackboard to make decisions, tool calls, and evidence flows traceable and evaluable while limiting memory contamination.

**ByteDance Seed AI4Math Research Internship** (Nov. 2025-May 2026)

- **Role:** Research Intern, AI Agent Development
- **MathNL TTS multi-agent reasoning:** Built a test-time-scaling system on the Seed 2.0 model family for olympiad mathematics. Designed Planner, Solver, and Verifier collaboration for strategy generation, parallel solving, proof verification, and backtracking; completed 5 iterations over 100+ problems and averaged 6.4/7 on an IMO problem set.
- **Automated Lean 4 proof QA:** Led a workflow combining static rules, code retrieval, and LLM-as-a-judge evaluation. Produced 600+ formalized data items and improved expert review efficiency by 70%+.
- **Evaluation-data operations:** Standardized SOPs for selection, classification, correctness, difficulty, expert annotation, and QA; delivered 2,000+ data items and authored 11 production and quality specifications.

**Low-Dimensional Spatiotemporal Dynamics of the Human Brain** (BIT, Dec. 2023-Present)

- **Role:** Project Lead; **Advisor:** Prof. Guoyuan Yang
- First applied complex principal component analysis to resting-state cerebellar fMRI and identified three dominant sparse patterns that jointly capture zero-lag spatial structure and time-lag dynamics. Validated robustness through network features, sequence reconstruction, and modularity analysis.
- Applied sCCA and linear SVMs to link individualized cerebellar activity with age, sex, cognition, and emotion.
- **Output:** 2 manuscripts, including a first-author article in *Nature Communications* and one manuscript under review.

**Complex Social Awareness Modeling** (SWU, Apr. 2022-Nov. 2024)

- **Role:** Project Lead; **Advisor:** Prof. Libo Zhang
- Modeled expert influence and isolation behavior in epidemic prevention using prospect and regret theories. Random-network simulations quantified intervention benefits and revealed phase transitions in social awareness.
- **Output:** 2 published papers, including a first-author article in *Nonlinear Dynamics* and a CCF Class C paper.

**Intelligent Factory Security** (SWU, Apr. 2022-Sep. 2023)

- **Role:** Project Lead; **Advisor:** Prof. Mingyang Zhong
- Developed adaptive multimodal identity recognition for faces under abnormal illumination or occlusion and voices in noise. Used three-way decisions (accept, reject, defer) to exploit visual and audio uncertainty estimates.
- **Award:** National First Prize, 2023 China Robot and Artificial Intelligence Competition.

**Large Language Model for Early Childhood Education** (SWU, Dec. 2023-Oct. 2024)

- **Role:** Research Project; **Advisor:** Prof. Libo Zhang
- Built a personalized multimodal teaching-material generation system on vivo's BlueLM, covering content generation, interactive dialogue, and AI-assisted drawing.
- **Award:** National First Prize, 2024 China Collegiate Computing Contest - AIGC Innovation Track.

**Xiangqi Game-Playing System** (SWU, Apr. 2021-Aug. 2021)

- **Role:** Project Lead; **Advisor:** Prof. Shenglin Li
- Implemented a Java Chinese chess engine using a pruned alpha-beta search tree, custom search and evaluation functions, human-vs-computer play, and game-record storage.
- **Award:** National Second Prize, 2022 Chinese Computer Game Championship.

</details>
```

- [ ] **Step 2: Replace the Chinese Recent Projects include**

Use this complete content:

```markdown
<span class='anchor' id='projects'></span>
<details markdown="1">
<summary style="cursor: pointer; font-size: 1.25em; margin-bottom: 8px;">🚀 <strong>近期项目</strong> <span style="font-weight: normal; opacity: .7;">（7 个项目 — 点击展开）</span></summary>

**通用网安智能体**（西南大学，2026.06-至今）

- **角色：** 项目负责人；**导师：** Prof. Libo Zhang
- 基于 LangGraph 构建 5 类专业 Agent 和 16 节点有界状态机，面向代码审计、渗透测试、应急响应与逆向分析，将 LLM 的任务理解、动态规划和反思能力同明确的权限、路由及退出规则解耦。
- 设计 R0-R3 风险分级、Finding-Evidence 验证机制、高风险操作人工审批，以及状态-领域黑板双层协作架构，使 Agent 决策、工具调用与证据流转可追踪、可解释、可评估，并降低错误记忆对后续决策的污染。

**字节跳动 Seed AI4Math 研究实习**（2025.11-2026.05）

- **角色：** AI Agent 研发实习生
- **MathNL TTS 多智能体推理：** 基于 Seed 2.0 系列模型开发数学竞赛题 Test-Time Scaling 系统，设计 Planner、Solver、Verifier 等角色协作完成候选策略生成、并行求解、证明验证与失败路径回溯；迭代 5 个版本，覆盖 100 题以上，在 IMO 习题评测中取得 6.4/7 平均分。
- **Lean 4 形式化证明自动质检：** 主导融合静态规则、代码检索与 LLM-as-a-judge 的自动化工作流，生产 600+ 条形式化数据，推动专家质检效率提升 70%+。
- **评测数据生产运维：** 围绕数据筛选、任务分类、正确性、难度、专家标注与质检流程建立标准化 SOP，交付 2,000+ 条数据并撰写 11 份数据生产与质量规范。

**低维人脑时空动态**（北京理工大学，2023.12-至今）

- **角色：** 项目负责人；**导师：** Prof. Guoyuan Yang
- 首次应用复主成分分析对小脑静息态 fMRI 数据建模，获得 3 个主要稀疏表征模式，同时捕获复杂活动的空间（zero-lag）与时间（time-lag）信息，并通过功能网络特征、序列重建和模块划分验证群体层面的鲁棒性。
- 应用 sCCA、线性 SVM 等可解释方法，建立个体小脑活动与年龄、性别、认知、情感等特征之间的关联。
- **成果：** 相关论文 2 篇，包括 1 篇一作 *Nature Communications* 论文和 1 篇在审稿件。

**复杂社会意识建模**（西南大学，2022.04-2024.11）

- **角色：** 项目负责人；**导师：** Prof. Libo Zhang
- 基于前景理论与后悔理论，对疾病防控中的专家影响与隔离行为进行建模；随机网络模拟量化了人为干预的防疫效益，并揭示社会意识的相变现象。
- **成果：** 已发表论文 2 篇，包括 1 篇一作 *Nonlinear Dynamics* 论文和 1 篇 CCF-C 论文。

**工厂智慧安防**（西南大学，2022.04-2023.09）

- **角色：** 项目负责人；**导师：** Prof. Mingyang Zhong
- 面向异常光照、遮挡条件下的人脸识别与嘈杂环境中的声纹识别，设计自适应多模态身份识别方法；通过接受、拒绝、延迟三支决策域利用视觉与听觉模块的不确定性度量。
- **奖项：** 2023 年中国机器人及人工智能大赛全国一等奖。

**幼教大模型**（西南大学，2023.12-2024.10）

- **角色：** 科研项目；**导师：** Prof. Libo Zhang
- 基于 vivo 自研蓝心大模型（BlueLM）构建个性化多模态教材生成系统，涵盖教学内容生成、交互式对话与 AI 辅助绘图。
- **奖项：** 2024 年中国高校计算机大赛-AIGC 创新赛全国一等奖。

**中国象棋博弈系统**（西南大学，2021.04-2021.08）

- **角色：** 项目负责人；**导师：** Prof. Shenglin Li
- 使用 Java 实现中国象棋博弈系统，基于剪枝的 alpha-beta 搜索树设计搜索与评估函数，并实现人机对战和棋谱保存功能。
- **奖项：** 2022 年中国计算机博弈锦标赛全国二等奖。

</details>
```

- [ ] **Step 3: Update both homepage timestamps**

Change the footer strings to:

```html
<em>Last updated: Sep. 2026</em>
```

and:

```html
<em>最后更新：2026 年 9 月</em>
```

- [ ] **Step 4: Run the complete feature test**

Run: `python3 -m unittest tests/test_cv_projects_update.py -v`

Expected: all five tests PASS.

- [ ] **Step 5: Commit the bilingual project update**

```bash
git add _pages/includes/recent_projects.md _pages/includes/zh/recent_projects.md _pages/about.md _pages/zh.md
git commit -m "feat: align recent projects with September CVs"
```

### Task 4: Verify the complete bilingual site

**Files:**
- Verify: all files changed in Tasks 1-3
- Verify: `_site/index.html`
- Verify: `_site/zh/index.html`

**Interfaces:**
- Consumes: the finished Jekyll source and assets.
- Produces: a successful test/build record and generated bilingual pages with valid CV links and rendered project content.

- [ ] **Step 1: Confirm the published PDFs still match the source files**

```bash
cmp -s '/Users/shuolv/Desktop/Code/Secmind/output/pdf/Shuo_Lv_Academic_CV_Template.pdf' assets/files/CV202609_EN.pdf
cmp -s '/Users/shuolv/Desktop/personal materials/202609北京理工大学-吕硕-个人简历-副本.pdf' assets/files/CV202609_ZH.pdf
```

Expected: both commands exit 0.

- [ ] **Step 2: Run the complete source test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 3: Build the Jekyll site**

Run: `bundle exec jekyll build`

Expected: exit code 0 and generated English/Chinese pages under `_site/`.

- [ ] **Step 4: Inspect generated homepage contracts**

```bash
python3 - <<'PY'
from pathlib import Path

contracts = {
    Path("_site/index.html"): (
        "(7 projects — click to expand)",
        (
            "General-Purpose Cybersecurity Agent",
            "ByteDance Seed AI4Math Research Internship",
            "Low-Dimensional Spatiotemporal Dynamics of the Human Brain",
            "Complex Social Awareness Modeling",
            "Intelligent Factory Security",
            "Large Language Model for Early Childhood Education",
            "Xiangqi Game-Playing System",
        ),
        ("Smart Cultural Tourism", "Leadership Evaluation Framework"),
    ),
    Path("_site/zh/index.html"): (
        "（7 个项目 — 点击展开）",
        (
            "通用网安智能体",
            "字节跳动 Seed AI4Math 研究实习",
            "低维人脑时空动态",
            "复杂社会意识建模",
            "工厂智慧安防",
            "幼教大模型",
            "中国象棋博弈系统",
        ),
        ("智慧文旅", "多基因风险下的领导力评估"),
    ),
}
for path, (summary, titles, obsolete_titles) in contracts.items():
    html = path.read_text(encoding="utf-8")
    assert "/assets/files/CV202609_EN.pdf" in html, path
    assert "/assets/files/CV202609_ZH.pdf" in html, path
    assert summary in html, path
    positions = [html.index(title) for title in titles]
    assert positions == sorted(positions), path
    for title in obsolete_titles:
        assert title not in html, (path, title)
    assert "**General-Purpose" not in html, path
    assert "**通用网安智能体" not in html, path
print("generated homepage contracts passed")
PY
```

Expected: `generated homepage contracts passed`.

- [ ] **Step 5: Check patch hygiene and repository state**

Run: `git diff --check && git status --short`

Expected: no whitespace errors; only intentional pre-existing user changes, if any, remain uncommitted.
