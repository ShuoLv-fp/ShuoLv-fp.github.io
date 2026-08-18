# 个人主页海外博士申请向优化方案（含中英双语）

## 概述 (Summary)

将现有 Jekyll 学术主页（AcadHomepage 模板，站点 `ShuoLv-fp.github.io`）优化为面向 2027 Fall 海外 PhD 申请的学术型主页，并提供**中英双语 + 一键切换**。核心工作分五块：

1. **清除模板残留**：SEO 元信息仍指向模板作者 "Xiaolong Luo, Harvard University"，多个 include 文件残留模板作者内容，`_config.yml` 域名仍是模板域名 —— 全部修正/删除。
2. **中英双语**：新增中文版主页（`/zh/`），导航栏加"中文/EN"一键切换按钮，英文与中文各用一套导航与内容板块。
3. **Publications 板块配图**：为 6 篇论文获取正文配图（图 1），本地化存储并在论文条目左侧展示；无法自动获取的（bioRxiv、AAAI、CCSCW）留占位并给出替换指引。
4. **页面结构重排**：新增真实 News 板块，按 `News → Publications → Research → Projects → Education → Awards → Skills → Teaching → Passions(折叠) → Contact` 重排，全部区块加显式锚点。
5. **其他美化**：修复侧栏失效链接、修正论文条目错误（空链接、错误日期、多余星号）、Passions 折叠置底、补充 research keywords 与 hreflang 等 SEO 信息。

站点为 Jekyll + GitHub Pages，用 `bundle exec jekyll serve` 本地验证。

## 现状分析 (Current State Analysis)

站点为 Jekyll 静态站，主页内容在 `_pages/about.md`，通过 `{% include_relative includes/xxx.md %}` 拼装各板块；导航由 `_includes/masthead.html` 渲染 `site.data.navigation.main`，侧栏由 `_includes/author-profile.html` 渲染 `site.author` 配置。已确认的问题：

**A. 模板残留（最严重）**
- `_includes/custom-head.html` 的 keywords、`citation_institution`、`citation_department` 仍写 "Xiaolong Luo / Harvard University / SEAS"，搜索引擎会把主页识别为模板作者。
- `_config.yml` 第 13 行 `url: "https://aaronluo00.github.io"`（模板作者域名），导致 sitemap/canonical/og:url 全错。
- `_pages/includes/` 下 `intro.md`、`pub_short.md`（Yi Ren 的语音论文列表）、`others.md`、`services.md`、`extracurricular.md`、`homepage.md`、`news.md`（哈佛作者新闻）均为模板内容且未被任何页面 include（已 grep 确认）。
- `_pages/includes/professional_service.md` 含 CVPR/ICLR/NeurIPS 审稿记录 —— **用户已确认非本人经历**，须删除。
- `.github/FUNDING.yml` 是模板作者 RayeRen 的赞助配置；`assets/blog_posts/` 是哈佛作者博客文章（`_pages/blog.md` 已重定向到外部博客，全站无引用）。
- `images/500x300.png`、`assets/icons/temp-icon*.html` 为模板占位/临时文件。
- `CLAUDE.md` 第 79-80 行、`README.md` 仍描述模板作者仓库。

**B. 配置/链接错误**
- `google_analytics_id: "VAsm0T8AAAAJ&hl"` 是 Google Scholar ID 而非 GA ID（且 `analytics.html` 未被任何布局 include，为死配置）。
- `description: ""` 为空，侧栏无站点描述。
- LinkedIn 值是完整 URL，但 `author-profile.html` 会自动加前缀 `https://www.linkedin.com/in/`，渲染出错误链接。
- Steam 同理会拼出 `https://steamcommunity.com/id/https://...` 错误链接（模板前缀是 `/id/`）。
- ORCID 用了 `my-orcid` 占位 URL。
- `bilibili`、`zhihu`、`xiaohongshu`、`cloudmusic` 四个键在 `author-profile.html` 中无对应渲染分支，属死配置（不显示，保留值不动）。
- `_includes/head.html` 内嵌非法 `<head><base target="_blank"></head>`，导致全站链接新标签打开（导航跳转体验差）；`run_server.sh` 中 `jekyll liveserve` 是错误命令。

**C. 论文条目问题（`_pages/includes/pub.md`）**
- CCSCW 论文链接为空 `[]()`；AAAI 链接带 `#:~:text=` 文本片段；AAAI 日期 "Jan. 2026" 与实际出版日期（OJS 显示 2026-03-14）不符；脚注末尾多一个游离星号。

**D. 结构问题**
- 无 News 板块（且现有 `news.md` 是模板内容）；导航锚点依赖 kramdown emoji 标题自动生成 ID（脆弱）；Publications 无配图，纯文字列表，视觉单调。

**E. 配图可获取性（已核实）**
| 论文 | 图源 URL（均已验证 HTTP 200） | 结论 |
|---|---|---|
| ① Nat Commun 小脑 | `https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41467-026-72931-6/MediaObjects/41467_2026_72931_Fig1_HTML.png` | 可下载。注意：该文为 early-access 未编辑版，正式排版后文件名可能变化 |
| ② Nonlinear Dynamics | `https://media.springernature.com/full/springer-static/image/art%3A10.1007%2Fs11071-023-09146-7/MediaObjects/11071_2023_9146_Fig1_HTML.png` | 可下载 |
| ③ bioRxiv 自闭症 | 页面可达，但脚本直连图被限流（429）；图 URL 惯例为 `https://www.biorxiv.org/content/biorxiv/early/2025/10/23/2025.10.23.684286v1/F1.large.gif` | 尝试带浏览器 UA 下载；失败则占位 + 手动指引 |
| ④ Comms Bio IHFPs | `https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs42003-025-08509-7/MediaObjects/42003_2025_8509_Fig1_HTML.png` | 可下载 |
| ⑤ AAAI BrainLMM | OJS 页面无内嵌图；PDF galley 可下载：`https://ojs.aaai.org/index.php/AAAI/article/download/42413/46374` | 下载 PDF 渲染后裁剪图 1；失败则占位 |
| ⑥ ChineseCSCW | 无在线论文页（Springer CCIS 2910/2911 论文集 2026-08 上市，章节 DOI 未收录） | 占位图 + TODO 注释 |

## 具体修改 (Proposed Changes)

### 1. 修复 SEO 与配置（`_config.yml`、`_includes/custom-head.html`）

**`_config.yml`**：
- 第 13 行 `url` → `"https://ShuoLv-fp.github.io"`。
- 第 10 行 `description` → `"Master's student at Beijing Institute of Technology. Research on computational neuroscience, large language models, and complex networks. Seeking Ph.D. positions for Fall 2027."`
- 第 17 行 `google_analytics_id` → `""`（死配置，置空并注释说明）。
- 第 52 行 ORCID → `"https://orcid.org/0009-0009-2540-0485"`。
- 第 50 行 LinkedIn → 只保留 slug：`"%E7%A1%95-%E5%90%95-793613399"`（模板自动补前缀）。
- 第 59 行 `steam` 键 → 删除（模板前缀 `/id/` 与数值 ID 不兼容，渲染必然出错；学术侧栏价值低）。
- `employer2: "Bytedance"` → **保留**（用户确认仍在职/有合作）。
- `title` → 可选改为 `"Shuo Lv | Computational Neuroscience & AI for Science"`。

**`_includes/custom-head.html`**：
- keywords → `"Shuo Lv, Beijing Institute of Technology, Computational Neuroscience, Cognitive Neuroscience, fMRI, Large Language Models, Complex Networks, AI for Science"`。
- `citation_institution` → `"Beijing Institute of Technology"`。
- `citation_department` → `"School of Interdisciplinary Science"`。
- 追加 hreflang 交替链接：`{% if page.lang == 'zh' %}<link rel="alternate" hreflang="en" href="{{ site.url }}{{ site.baseurl }}/">{% else %}<link rel="alternate" hreflang="zh" href="{{ site.url }}{{ site.baseurl }}/zh/">{% endif %}`。

### 2. 中英双语 + 一键切换（新增中文版主页）

**2.1 新增中文主页 `_pages/zh.md`**
- front matter：`permalink: /zh/`、`title: ""`、`author_profile: true`、`lang: zh`、`excerpt: ""`。
- 内容结构与 `about.md` 完全镜像：中文 intro 段落 + 两条横幅（"积极寻找 2027 Fall AI for Science / 计算神经科学方向 PhD 机会"）+ `{% include_relative includes/zh/news.md %}`、`zh/pub.md`、`zh/research_interests.md`、`zh/recent_projects.md`、`zh/education.md`、`zh/honers.md`、`zh/technical_skills.md`、`zh/teaching.md`、`zh/passions.md` + 底部"合作者与联系" + "最后更新：2026年8月"。
- 论文标题、作者、期刊名保持英文（学术惯例），板块标题与说明文字用中文。

**2.2 新增中文 include 目录 `_pages/includes/zh/`（11 个文件）**
- `education.md`（北京理工大学/西南大学，校徽图片复用 `/_pages/includes/images/` 下的 BIT.svg、SWU.svg）、`research_interests.md`（🔬 研究方向，译文）、`pub.md`（📝 论文，含锚点 `id='publications'` 与"左图右文"布局，译文说明 + 英文论文信息）、`recent_projects.md`（🚀 研究项目，译文）、`honers.md`（🏆 荣誉奖项，译文）、`technical_skills.md`（💻 技能，译文）、`teaching.md`（👨🏫 教学经历，译文，含锚点 `id='teaching'`）、`passions.md`（🎤 个人兴趣，`<details>` 折叠，译文）、`news.md`（🔥 新闻，译文）、`vision.md`（🎯 研究愿景，用户原文翻译，措辞待用户审阅）。
- 各文件顶部沿用 `<span class='anchor' id='...'></span>` 显式锚点（news/publications/research/projects/education/awards/skills/teaching），锚点 id 与英文版一致（同一页面内仅一份导航，见 2.3）。

**2.3 导航与切换按钮（`_data/navigation.yml` + `_data/navigation-zh.yml` + `_includes/masthead.html`）**
- 新建 `_data/navigation-zh.yml`（`main_zh`）：中文标题 + `/zh/#xxx` 锚点链接，条目与英文版一一对应：首页/新闻/论文/研究/项目/教育/荣誉/技能/教学/联系。
- `_data/navigation.yml`（`main`）更新为：About(`/#about-me`)、News(`/#news`)、Publications(`/#publications`)、Research(`/#research`)、Projects(`/#projects`)、Education(`/#education`)、Awards(`/#awards`)、Skills(`/#skills`)、Teaching(`/#teaching`)、Contact(`/#contact`)。
- `_includes/masthead.html`：
  - 第 7 行 "Homepage" 链接改为按语言条件渲染：`{% if page.lang == 'zh' %}主页 → {{ site.baseurl }}/zh/#about-me{% else %}Homepage → {{ site.baseurl }}/#about-me{% endif %}`。
  - 第 8 行导航循环改为按 `page.lang` 选择数据源：`{% assign nav = site.data.navigation.main %}{% if page.lang == 'zh' %}{% assign nav = site.data.navigation.main_zh %}{% endif %}`，URL 渲染逻辑不变。
  - 在 dark-mode-toggle 前新增语言切换按钮：`{% if page.lang == 'zh' %}<li class="masthead__menu-item"><a href="{{ site.baseurl }}/">EN</a></li>{% else %}<li class="masthead__menu-item"><a href="{{ site.baseurl }}/zh/">中文</a></li>{% endif %}`（用与导航一致的 `<li>` 样式，加 `lang-switch` 类以便微调间距）。
- `_pages/about.md` front matter 增加 `lang: en`。
- `_layouts/default.html` 第 6 行 `<html lang="en">` → `<html lang="{{ page.lang | default: 'en' }}">`。
- 切换按钮仅出现在设置了 `page.lang` 的页面（about/zh），其余页面（teaching、philosophy、blog 重定向页）不显示，控制范围避免维护爆炸。

### 3. Publications 板块配图（新增 `images/pub/`，重写 `pub.md` 与 `zh/pub.md`）

**图片获取与本地化**（全部存入 `/Users/shuolv/Documents/GitHub/ShuoLv-fp.github.io/images/pub/`，PNG，展示宽 160–200px；中英文两版共用同一批图片）：
1. `pub_natcommun_cerebellum.png` ← 从 ① 的 media.springernature.com URL 下载（`curl -L`）。
2. `pub_nd_experts.png` ← 从 ② 的 URL 下载。
3. `pub_biorxiv_autism.png` ← 先尝试 `curl -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"` 抓 F1.large.gif；若仍 429，则生成占位图 `pub_biorxiv_autism_placeholder.png`（灰底 + "Figure 1 — replace with bioRxiv Fig.1"），并在交付说明中写明：在浏览器打开论文页 `https://www.biorxiv.org/content/10.1101/2025.10.23.684286v1` 右键保存图 1（或下载全文 PDF 裁剪）后替换同名文件。
4. `pub_commsbio_ihfp.png` ← 从 ④ 的 URL 下载。
5. `pub_aaai_brainlmm.png` ← 下载 PDF galley，用 `pdftoppm`（若未安装则 `brew install poppler`）渲染首页为 PNG，再用 Python PIL 按第一张图位置裁剪；若环境无 poppler，则生成占位图并写明替换方式（从 AAAI PDF 中截取 Fig.1 语义映射图）。
6. `pub_ccscw_placeholder.png` ← 用 Python PIL 生成占位图（灰底 + "Figure coming soon — paper in Springer CCIS 2910"），并在 pub.md/zh/pub.md 加 HTML 注释 `<!-- TODO: 待 Springer CCIS 章节 DOI 上线后补链接与正式图 -->`。

**`pub.md` / `zh/pub.md` 重写要点**：
- 顶部加 `<span class='anchor' id='publications'></span>`，标题 `# 📝 Publications`（中文版 `# 📝 论文发表`）。
- 每篇论文用"左图右文"两栏结构：`<div style="display:flex; gap:20px; margin:18px 0; align-items:flex-start;">` 内放 `<a href="论文链接" target="_blank"><img src="/images/pub/xxx.png" style="width:160px; border-radius:6px; border:1px solid #ddd;" alt="..."></a>` 与右侧文字（标题加粗链接 + 作者（本人加粗）+ 期刊/会议 + [Code]/[PDF] 徽标，外链加 `target="_blank"`）。图统一本地化。
- 修正：脚注末尾游离 `*` 删除；AAAI 链接去掉 `#:~:text=` 片段；AAAI 时间改为 "Mar. 2026"；CCSCW 空链接指向会议页 `https://conf.ccf.org.cn/web/api/m1413311151097384960175700123647.action`。
- 本人署名的论文在作者列表中用 `<strong>Shuo Lv</strong>` 高亮；中文版标注"共同一作/通讯"说明（† 共同一作，* 通讯作者）。

### 4. 新增 News 板块（重写 `news.md` 与 `zh/news.md`）

顶部 `<span class='anchor' id='news'></span>`，标题 `# 🔥 News`（中文 `# 🔥 新闻`），按时间倒序（置顶一条用模板已有的红色高亮样式）：
- 置顶：英文版 `I am actively seeking Ph.D. positions in AI for Science / computational neuroscience for Fall 2027. Feel free to reach out!`；中文版对应译文。与 about.md/zh.md 顶部横幅呼应。
- `[2026.05]` 小脑论文发表于 *Nature Communications*（附链接）。
- `[2026.03]` BrainLMM 被 AAAI-26 录用/出版（附链接）。
- `[2025.11]` ChineseCSCW 2025 论文录用。
- `[2025.11]` 自闭症语言网络论文预印本上线 bioRxiv（附链接，在审）。
- `[2025.07]` IHFPs 论文发表于 *Communications Biology*（附链接）。

### 5. 主页结构重排（`_pages/about.md` 与 `_pages/zh.md` 同步）

- include 顺序改为：`intro 段落 → News → Publications → Research Interests → Recent Projects → Education → Honors & Awards → Technical Skills → Teaching → Passions(折叠) → Collaborators & Contact`（中英文一致）。
- 文案更新（英文版）：首段 "second-year Master student" → "a Master's student at Beijing Institute of Technology（2024–Present）"；蓝色横幅 "looking for summer 2026 internships" → "seeking Ph.D. positions for Fall 2027"（红/蓝两条横幅保留样式，与 CLAUDE.md 的高亮框规范一致）；末尾 "Last updated: Jun. 2026" → "Aug. 2026"。中文版对应翻译。
- 顶部保留 `# 💡Collaborators and friends` 与 `# 📧 Contact`（加 `<span class='anchor' id='contact'></span>`；中文版 `# 💡合作者与朋友`、`# 📧 联系`）。

**各 include 板块锚点补齐**（统一用 `teaching.md` 现有的 `<span class='anchor' id='xxx'></span>` 写法，避免依赖 kramdown emoji 自动 ID；中英文 id 一致）：
- `news.md` → `id='news'`；`pub.md` → `id='publications'`；`research_interests.md` → `id='research'`；`recent_projects.md` → `id='projects'`；`education.md` → `id='education'`；`honers.md` → `id='awards'`；`technical_skills.md` → `id='skills'`（英文版标题由 "Technical Skills" 简化为 "Skills"，中文版 "技能"；内容可选补充 PyTorch、fMRIPrep、Nilearn、FSL 等神经影像工具）；`teaching.md` 已有 `id='teaching'`。

**Passions 折叠置底**（`passions.md` 与 `zh/passions.md`）：内容外包一层 `<details><summary>🎤 Passions & Hobbies</summary>...原内容...</details>`（中文版 `<details><summary>🎤 个人兴趣</summary>...`），默认收起，不加 JS 依赖。

**新增 Research Vision 段落**：采用 `_pages/includes/long_term_vision.md` 中用户本人文字，英文版标题 `# 🎯 Research Vision`（放 intro 之后、News 之前），文案微调对齐实际研究方向（脑动力学 + AI for Science + 复杂系统），保留用户原意，交付后由用户审阅措辞；中文版 `zh/vision.md` 对应译文。`long_term_vision.md` 文件保留。

### 6. 导航更新汇总

- `_data/navigation.yml`：见 2.3，全部改用显式锚点 `/ #xxx`。
- `_data/navigation-zh.yml`（新增）：见 2.3。
- 删除旧的 `/#-xxx` 自动锚点写法。

### 7. 模板残留清理（删除文件）

- `_pages/includes/intro.md`、`pub_short.md`、`others.md`、`services.md`、`extracurricular.md`、`homepage.md`、`professional_service.md`（用户确认非本人经历）。
- `.github/FUNDING.yml`（RayeRen 赞助配置）。
- `assets/blog_posts/` 整个目录（哈佛作者博客，全站无引用）。
- `images/500x300.png`、`assets/icons/temp-icon.html`、`assets/icons/temp-icon-small.html`。
- `README.md` 重写为简述本仓库用途的最小 README；`CLAUDE.md` 第 79-80 行模板仓库信息更新为 `ShuoLv-fp/ShuoLv-fp.github.io`，并补充双语维护说明（英文内容在 `includes/`，中文在 `includes/zh/`，两版需同步更新）。
- `LICENSE` **保留**（模板代码的 MIT 许可，保留符合法律规范）。
- `_config.yml` 的 `bilibili/zhihu/xiaohongshu/cloudmusic` 死配置键：保留值不动（不渲染、无害），仅注释说明。

### 8. 小修

- `run_server.sh`：`jekyll liveserve` → `jekyll serve`。
- `_includes/head.html`：移除非法嵌套 `<head><base target="_blank"></head>`，恢复标准链接行为（同标签页跳转）；外链（论文、代码、侧栏社交链接）在各自 `<a>` 上加 `target="_blank"` 保持新标签打开。
- 侧栏（`author-profile.html`）标签保持英文（CV/Email/Location 等为通用词，中英页面共用，不做翻译以控制改动面）。

## 假设与决策 (Assumptions & Decisions)

- **语言**：英文为默认（海外申请惯例），中文为 `/zh/` 镜像版；学术内容（论文标题/作者/期刊名）在两版均保持英文，仅叙述性文字翻译。
- **切换按钮**：置于导航栏末尾（暗色模式按钮旁），仅在有 `page.lang` 的主页显示；其余页面不显示（控制维护范围）。
- **News 置顶横幅**：文案假定申请 2027 Fall 入学；如需调整可在执行时改措辞。
- **bioRxiv / AAAI 图**：优先自动下载；环境受限时留占位图并在最终回复中给出"在哪一块替换哪张图"的明确指引（对应 `images/pub/` 下的文件名，中英文版指向同一图片）。
- **Research Vision 文案**：以用户原文为主、微调对齐研究主题，措辞需用户最终审阅。
- **侧栏不翻译**：避免大范围改动共享模板，保持中英两版侧栏一致（英文标签）。
- **git 提交与推送**：本地验证通过后 `git add/commit` 并 `git push` 触发 GitHub Pages 自动部署（站点为此仓库唯一线上内容，属预期动作）。

## 验证 (Verification)

1. `bundle exec jekyll build` 无报错（含删除文件后无引用断裂、`zh.md` 与 `zh/` includes 全部正常渲染）。
2. `bundle exec jekyll serve` 本地预览：
   - 访问 `/` 与 `/zh/`，点击导航栏"中文/EN"切换按钮，两版互跳正常。
   - 英文版与中文版各导航锚点（News/Publications/Research/Projects/Education/Awards/Skills/Teaching/Contact）逐一点击确认跳转到**当前语言页面对应板块**（英文 `/ #xxx`，中文 `/zh/#xxx`）。
   - 检查 6 张论文配图正常显示（含占位图），暗色模式（`assets/js/dark-mode.js`）下图片带边框不刺眼。
3. 侧栏链接逐一点开：LinkedIn（`https://www.linkedin.com/in/%E7%A1%95-%E5%90%95-793613399/`）、ORCID、Email、CV（`CV202606.pdf`）、Google Scholar、WeChat 二维码。
4. 页面源码检查：`<html lang>` 按页面语言输出正确；hreflang 交替链接存在；已无 "Xiaolong Luo / Harvard / AaronLuo00 / RayeRen" 等模板痕迹（grep 校验，LICENSE 除外）。
5. `git push` 后访问线上 `https://ShuoLv-fp.github.io/` 与 `https://ShuoLv-fp.github.io/zh/` 复核渲染、切换与 sitemap。
