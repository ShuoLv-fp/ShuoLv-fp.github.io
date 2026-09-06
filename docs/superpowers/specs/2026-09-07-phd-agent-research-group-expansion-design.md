# PhD Agent Research Group Expansion: Design Specification

**Date:** 2026-09-07  
**Status:** Approved in conversation; awaiting written-spec review  
**Repository:** `ShuoLv-fp/ShuoLv-fp.github.io`

## 1. Objective

Expand the password-protected PhD Application Agent with at least 100 newly researched, non-duplicate research-group leads outside the United States and Canada. Every new lead must concern AI agents, neuroscience, AI for Science, or a closely related intersection, and must be evaluated against Shuo Lv's existing research record.

The expansion is a discovery and evaluation pass. It does not generate outreach-email drafts for the new records.

## 2. Existing State

- The current private seed contains 93 faculty records.
- Twenty-eight records currently have a positive `featured_rank` and therefore appear as full advisor dossiers in the protected interface.
- Existing online notes, statuses, artifacts, and revision history are authoritative and must not be overwritten by an old local snapshot.
- The public repository must remain free of production faculty data and research-profile content that belongs in private Cloudflare storage.

## 3. Research Scope

### 3.1 Geographic rule

Exclude every research group whose primary institution is in the United States or Canada. Nationality is irrelevant; the location of the research group's primary institution controls inclusion.

Institutions in the United Kingdom, continental Europe, Switzerland, Australia, New Zealand, Singapore, Hong Kong SAR, mainland China, Japan, South Korea, India, Israel, the Middle East, Africa, and Latin America are eligible.

### 3.2 Subject rule

Each retained group must have current official evidence for at least one of these areas:

1. AI agents, multi-agent systems, autonomous scientific workflows, tool-using language models, formal reasoning, theorem proving, or test-time reasoning;
2. computational, cognitive, systems, network, or clinical neuroscience, especially neuroimaging, brain dynamics, functional organization, the cerebellum, visual cortex, or individualized brain analysis;
3. AI for Science, including scientific foundation models, automated discovery, computational biology, biomedical AI, scientific machine learning, or related agentic research;
4. complex systems and network science that materially overlaps Shuo's published work on contagion, epidemic dynamics, collective behavior, or coupled networks.

Broad AI, generic data science, purely wet-lab neuroscience, and unrelated clinical groups are excluded unless an official source demonstrates a concrete overlap with the target areas.

### 3.3 Quantity and quality target

- Discover approximately 140–160 plausible candidates.
- Retain at least 110 verified candidates when possible, providing a buffer above the user's minimum of 100.
- The final online append must contain at least 100 valid new records after deduplication against the authoritative cloud dataset.
- A preferred portfolio balance is approximately 40% Agent/AI4Science, 40% neuroscience, and 20% interdisciplinary or complex-systems work. Quality takes precedence over exact quotas.

## 4. Evidence and Deduplication

Each record requires at least one first-party source: an official university faculty page, official laboratory or institute page, or official personal academic page clearly tied to the institution. Secondary directories may be used for discovery but do not, by themselves, qualify a record for inclusion.

Each evidence item records its title, URL, verification date, and a short note describing what was confirmed. If a source is inaccessible or does not clearly support the claimed research area, exclude the candidate rather than infer missing facts.

Deduplicate against the live cloud data and within the new batch using:

1. normalized official homepage URL;
2. normalized PI or group-lead name plus institution;
3. normalized laboratory name plus institution, when the entry represents a group rather than an individual.

Homepage redirects and alternate institutional abbreviations count as the same record. Ambiguous same-name cases are resolved using department and official URL evidence.

## 5. Record Design and Fit Evaluation

Each new record contains:

- stable generated identifier;
- PI or research-group lead name;
- institution, short institution label, department, country, and region;
- entry type and official homepage URL;
- concise research area and research summary;
- specific keywords supported by the source;
- evidence with verification date;
- match analysis describing direct connections to Shuo's work, meaningful gaps or cautions, and the strongest conversation angle;
- numeric fit score, confidence level, and matched dimensions;
- `discovered` status, blank personal notes, and a creation/update timestamp;
- a positive `featured_rank` so the entry appears in the searchable dossier interface.

Fit scoring uses Shuo's existing profile weights:

- 45%: LLM agents, multi-agent scientific reasoning, AI4Science, mathematical reasoning, Lean, or formal verification;
- 35%: neuroimaging, spatiotemporal brain dynamics, cerebellum, functional parcellation, visual cortex, or computational neuroscience;
- 20%: complex networks, contagion, epidemic spreading, collective behavior, and nonlinear network dynamics.

Scores measure potential research alignment, not laboratory prestige. The explanation must identify concrete overlap with one or more of Shuo's publications, projects, skills, or research priorities. A group may score highly through one exceptionally strong dimension; it does not need to cover all three.

No outreach artifact is created for these records.

## 6. Safe Online Append Architecture

The local historical seed is used only to understand the schema and support preliminary deduplication. It must not overwrite the live workflow.

Add an authenticated administrative append route to the Cloudflare Worker. The route accepts only a bounded array of faculty records, validates every required field and field size, generates no arbitrary collection writes, and rejects United States or Canadian institution locations. It is protected by the existing migration secret and is not exposed in the normal user interface.

The `WorkflowCoordinator` performs the append as one serialized operation:

1. load the current authoritative workflow;
2. validate and normalize the submitted batch;
3. compare it with current records using the deduplication keys;
4. append only new records;
5. assign featured ranks after the current maximum without changing existing ranks;
6. increment the global revision once;
7. persist the new workflow and update the KV recovery snapshot;
8. return counts for submitted, appended, and skipped records without returning unrelated private content.

The endpoint refuses an empty batch, an oversized batch, malformed records, duplicate identifiers, invalid URLs, or forbidden countries. A repeated submission is idempotent because already-appended records are detected and skipped.

## 7. Interface Behavior

The existing interface and visual system remain unchanged. Newly appended records appear in the existing searchable dossier index because they receive positive featured ranks.

The dossier view displays the new group's identity, institution, research summary, official evidence, fit score, dimension matches, match analysis, and editable status/notes. The outreach section shows the existing empty state because no draft is linked.

Search remains client-side and must continue to work with at least the combined current and new record count. No new navigation, filters, routes, or public pages are added.

## 8. Error Handling and Recovery

- Research candidates with inadequate first-party evidence are omitted.
- Invalid records fail local validation before any remote mutation.
- The cloud append is atomic: validation or storage failure appends nothing.
- Duplicate records are reported as skipped rather than treated as errors.
- The authoritative workflow is exported or otherwise revision-checked immediately before the append so recent online edits are preserved.
- After the append, verify the new cloud revision and collection count through authenticated read-back without printing private records into repository files or logs.
- If deployment succeeds but the data append fails, leave the existing workflow intact, correct the batch or endpoint, and retry the idempotent append.

## 9. Verification and Acceptance Criteria

Automated checks cover:

- required record fields and fit-score bounds;
- official HTTP(S) homepage and evidence URLs;
- exclusion of United States and Canadian groups;
- duplicate identifiers and normalized homepage/name-institution keys;
- append-route authentication, request-size limits, and schema validation;
- atomic rejection of malformed batches;
- idempotent retry behavior;
- preservation of existing records, notes, statuses, artifacts, and featured ranks;
- new featured-rank allocation and revision increment;
- successful application tests and deployment dry run.

The work is accepted only when:

1. at least 100 new, verified, deduplicated research-group records have been appended to the authoritative online workflow;
2. every appended record is outside the United States and Canada;
3. every appended record contains a first-party source and an explicit profile-fit explanation;
4. existing online user edits and artifacts remain intact;
5. the new records appear in the protected searchable dossier interface;
6. no production research data, secret, temporary batch, or authenticated export is committed to the public repository;
7. the deployed protected application passes its existing tests and security checks.

## 10. Deliverables

- Deployed Worker code supporting safe, authenticated, idempotent faculty append operations.
- At least 100 new records added to the protected online webpage.
- A concise completion summary covering totals by country and research category, duplicate/quality exclusions, and verification results.
