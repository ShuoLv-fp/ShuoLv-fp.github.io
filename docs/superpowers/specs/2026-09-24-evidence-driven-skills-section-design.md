# Evidence-Driven Skills Section Design

**Date:** 2026-09-24  
**Status:** Approved for planning  
**Scope:** English and Chinese homepage Skills sections

## Objective

Transform the homepage Skills section from a flat tool list into a concise research profile that helps prospective Ph.D. advisors and collaborators understand three things quickly:

1. which capabilities are supported by published or shipped work;
2. which research directions Shuo wants to pursue next; and
3. which technical tools support that work.

The section should borrow the evidence-first information architecture of the referenced Expertise page without copying its presentation literally. It must remain visually consistent with the existing Jekyll homepage and work equally well in English, Chinese, light mode, dark mode, desktop, and mobile layouts.

## Chosen Approach

Use an evidence-driven research profile followed by a compact technical toolkit.

Two alternatives were considered and rejected:

- A capability matrix would expose cross-domain breadth, but it would be harder to scan on mobile and would not give publication or project evidence enough prominence.
- Interactive tabs would shorten the page, but they would hide important information from visitors who scan the homepage quickly.

The chosen approach keeps all high-value information visible and lets evidence, rather than arbitrary percentage scores, establish credibility.

## Information Architecture

The existing `#skills` anchor and navigation destination remain unchanged. The section will contain four parts in this order:

1. a short introduction explaining the evidence-first structure;
2. a “Demonstrated capabilities” / “已验证的能力” stack of three cards;
3. an “Exploring next” / “正在探索” grid of three lighter cards; and
4. a compact “Technical toolkit” / “技术工具箱” list.

The section will not include percentage progress bars or self-assigned numeric proficiency scores. Status labels will describe the type of experience instead: `Research-led`, `Published`, and `Built` in English, with equivalent Chinese labels.

## Demonstrated Capability Cards

Each capability card has one clear purpose: connect a capability claim to concrete evidence.

Every card contains:

- a title;
- one or more compact status labels;
- a two- or three-sentence summary written in outcome-first language;
- an evidence row with links to the relevant homepage section or external publication/project;
- a small group of technical keyword chips.

### 1. Computational Neuroscience and Neuroimaging

Emphasize spatiotemporal brain dynamics, individual differences, functional networks, and normative modelling.

Evidence will include the first-author *Nature Communications* work on cerebellar spatiotemporal patterns and the accepted *Translational Psychiatry* work on autism network topography. Keywords may include `fMRI`, `cPCA`, `sCCA`, `Normative Models`, and `Network Neuroscience`.

### 2. LLM Agents and Formal Reasoning

Emphasize multi-agent reasoning, test-time scaling, proof verification, and evaluation-system design.

Evidence will point to the ByteDance Seed AI4Math research internship and the existing projects section. The summary may cite the completed system iterations, IMO-set result, Lean 4 proof-quality workflow, and evaluation-data work already described on the homepage. Keywords may include `Multi-Agent Systems`, `Test-Time Scaling`, `Lean 4`, `Verification`, and `LLM Evaluation`.

### 3. Complex Systems and Intelligent Applications

Emphasize complex-network modelling, collective dynamics, multimodal recognition, and applied AI systems.

Evidence will link to the *Nonlinear Dynamics* research and relevant award-winning projects. Keywords may include `Complex Networks`, `Dynamical Systems`, `Multimodal Learning`, `Three-Way Decisions`, and `AIGC`.

## Exploration Cards

Exploration cards describe intent rather than claiming verified mastery. They use shorter copy, no capability level, and a visually quieter treatment than demonstrated-capability cards.

The three directions are:

1. **Brain-inspired foundation models** — connecting neural representations, multimodal foundation models, and computational accounts of cognition.
2. **Autonomous agents for science** — building agents that can plan, use tools, verify reasoning, and advance scientific workflows.
3. **Trustworthy human–AI collaboration** — designing auditable, controllable agent systems with explicit evidence and human oversight.

Each card contains a short statement of intent and three or four keyword chips. Copy must clearly distinguish current exploration from completed accomplishments.

## Technical Toolkit

The existing tool inventory remains, but it is compressed into four labelled rows:

- Programming: Python, C++, Java, R, Lean, and HTML;
- Machine learning: PyTorch, scikit-learn, Hugging Face, NumPy/SciPy, Pandas, and PyTorch Geometric;
- Agents and language models: LangChain, LangGraph, LlamaIndex, vLLM, Ollama, MCP, multi-agent orchestration, and test-time scaling;
- Neuroimaging and research: fMRIPrep, Nilearn, FSL, PLINK, LaTeX, and Git.

Existing outbound links remain where useful. Decorative language icons are removed from the primary reading flow unless they improve recognition without adding visual noise.

## Visual Direction

The design extends the site’s current academic blue visual language rather than introducing a separate theme.

### Palette

- `Evidence blue` — `#224B8D`, the existing primary accent;
- `Signal blue` — `#3F72B8`, used sparingly for evidence rails and hover states;
- `Paper` — `#FFFFFF`, primary card surface in light mode;
- `Mist` — `#F4F7FB`, quiet secondary surface;
- `Ink` — `#253247`, high-contrast text;
- `Coral marker` — `#D95D4F`, reserved for a small “exploring” accent and never used as a broad gradient.

Dark-mode equivalents will use the site’s existing dark surface and text variables, with adjusted borders and chips that retain sufficient contrast.

### Typography

The section inherits the site typography to preserve visual continuity. Hierarchy comes from weight, size, spacing, and restrained uppercase utility labels rather than loading new web fonts.

### Layout

Demonstrated capabilities form a single-column stack so their evidence remains readable. Exploration cards form a three-column grid on wide screens and collapse to one column on narrow screens. The toolkit uses compact labelled rows and wraps naturally.

```text
Skills
Introductory sentence

DEMONSTRATED CAPABILITIES
┌────────────────────────────────────────────┐
│ title                         status chips │
│ outcome-focused summary                    │
│ evidence ━━━ link · link                   │
│ keyword  keyword  keyword                  │
└────────────────────────────────────────────┘
                 × 3

EXPLORING NEXT
┌────────────┐ ┌────────────┐ ┌────────────┐
│ direction  │ │ direction  │ │ direction  │
│ intent     │ │ intent     │ │ intent     │
└────────────┘ └────────────┘ └────────────┘

TECHNICAL TOOLKIT
Programming      Python · C++ · R · Lean
Machine learning PyTorch · Hugging Face · ...
```

### Signature Element

Each demonstrated-capability card has a thin horizontal “evidence rail” leading into its linked evidence chips. The rail visually connects claim and proof and becomes the memorable element of the section. It is structural rather than decorative.

Hover motion is limited to a subtle border and elevation change. Reduced-motion preferences disable transitions. The cards do not use animated progress bars.

## Component and File Boundaries

Content remains in the two existing include files:

- `_pages/includes/technical_skills.md`
- `_pages/includes/zh/technical_skills.md`

Shared styling is added to a focused Sass partial, `_sass/_skills.scss`, imported by `assets/css/main.scss`. No JavaScript is required.

Automated presentation tests will be extended in `tests/test_homepage_presentation.py` to verify that both languages contain the new structural class names, all three capability cards, the exploration grid, and the toolkit. Tests will also guard against percentage-based level bars returning later.

## Responsive and Accessible Behaviour

- Cards are readable without hover and contain no hover-only information.
- Evidence links use descriptive text and visible keyboard focus.
- Status labels are textual, so meaning does not depend on colour.
- Cards reflow without horizontal scrolling down to narrow mobile widths.
- Link and text contrast meet WCAG AA targets in light and dark modes.
- Decorative rails are hidden from assistive technology through CSS rather than extra semantic elements where possible.
- Print output remains legible and avoids heavy shadows or coloured backgrounds.

## Failure and Degradation Behaviour

The section is static HTML and CSS. If CSS fails, content remains in a logical reading order and all evidence links remain usable. If an external evidence link is unavailable, the claim is still understandable and internal homepage links continue to provide context. No content depends on client-side JavaScript.

## Verification

Implementation is complete when:

- both English and Chinese homepages contain matching structures and equivalent content;
- all six research cards and the compact toolkit render through Jekyll without errors;
- evidence links point to existing internal anchors or verified external pages;
- light mode, dark mode, desktop, and mobile layouts are visually checked;
- keyboard focus is visible on all interactive elements;
- reduced-motion and print rules behave sensibly;
- existing homepage tests and the new Skills tests pass; and
- no unrelated homepage sections change.

## Out of Scope

- A new standalone Expertise page;
- skill filtering, tabs, accordions, or other JavaScript interactions;
- numerical proficiency scores or progress bars;
- new analytics or backend services;
- rewriting publications, projects, or research sections outside the links needed by the Skills cards.
