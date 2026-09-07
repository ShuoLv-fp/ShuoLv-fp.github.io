import { access, readFile } from "node:fs/promises";

const researchRoot = new URL("../public/research/", import.meta.url);
const briefingPath = new URL("ewu-ultralow-field-mri.html", researchRoot);
const stylePath = new URL("ewu-ultralow-field-mri.css", researchRoot);
const figureRoot = new URL("ewu-ultralow-field-mri/", researchRoot);
const figures = [
  "whole-body-system.jpg",
  "whole-body-contrasts.jpg",
  "fast-brain-pipeline.jpg",
  "clinical-case-comparison.jpg",
  "emi-pipeline.jpg",
  "emi-comparison.jpg"
];

const briefing = await readFile(briefingPath, "utf8").catch(() => {
  throw new Error("Private research briefings are missing. Restore public/research before deployment.");
});
await access(stylePath);
await Promise.all(figures.map((name) => access(new URL(name, figureRoot))));

const paperCount = briefing.match(/<article class="paper-card"/g)?.length || 0;
const figureCount = briefing.match(/<figure class="evidence-figure"/g)?.length || 0;
if (paperCount !== 18 || figureCount !== figures.length) {
  throw new Error(`Private Wu Lab briefing is incomplete (${paperCount} papers, ${figureCount} figures).`);
}

console.log(`Private research briefing verified: ${paperCount} papers, ${figureCount} figures.`);
