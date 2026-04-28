// WOSAC Research Plan — UCL Bartlett-styled deck
// Built with pptxgenjs per the project's pptx skill methodology
//
// Run from repo root or from slides/:  node slides/build.js
// Output:  slides/dist/WOSAC_Research_Plan.pptx

const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = __dirname;                       // slides/
const ASSETS = path.join(ROOT, "assets");
const DIST = path.join(ROOT, "dist");
fs.mkdirSync(DIST, { recursive: true });

const A = (rel) => path.join(ASSETS, rel);    // asset path helper

const COL = {
  ucl: "500778",        // UCL Purple (dominant accent)
  uclDeep: "2E0344",    // darker for title-slide background
  ink: "1A1A1A",        // body text
  muted: "6B6B6B",      // captions, footer
  rule: "C8B8D6",       // soft purple rule
  soft: "F2EEF7",       // very light lilac, for section fills
  white: "FFFFFF",
  amber: "C8860D",      // sparingly used callout accent
};

const FONT = "Calibri";

const W = 13.333, H = 7.5;   // LAYOUT_WIDE — gives roomier academic feel

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "WOSAC Research Plan";
pres.title  = "Waymo Open Sim Agents Challenge — Research Plan";
pres.company = "UCL · The Bartlett";

// ---------- helpers ----------
function makeShadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 2, angle: 90, opacity: 0.10 };
}

// Common content-slide chrome: left sidebar, title, footer, page number
function addChrome(slide, opts) {
  const { pageNum, title } = opts;
  // Left sidebar motif (full-height thin purple bar)
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.18, h: H,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  // Title (no underline accent line — avoid AI-tell)
  if (title) {
    slide.addText(title, {
      x: 0.6, y: 0.45, w: W - 1.2, h: 0.75,
      fontFace: FONT, fontSize: 30, bold: true,
      color: COL.ucl, align: "left", valign: "middle", margin: 0,
    });
  }
  // Footer wordmark (bottom-left)
  slide.addText("WOSAC · Research Plan", {
    x: 0.6, y: H - 0.4, w: 6, h: 0.3,
    fontFace: FONT, fontSize: 9, color: COL.muted, align: "left", margin: 0,
  });
  // Page number (bottom-right)
  if (pageNum != null) {
    slide.addText(String(pageNum).padStart(2, "0"), {
      x: W - 1.2, y: H - 0.4, w: 0.6, h: 0.3,
      fontFace: FONT, fontSize: 10, color: COL.ucl, bold: true,
      align: "right", margin: 0,
    });
  }
}

// Bullet list helper — uses bullet: true (never unicode)
function bulletText(items) {
  const out = [];
  items.forEach((it, i) => {
    if (typeof it === "string") {
      out.push({ text: it, options: { bullet: true, breakLine: i < items.length - 1 } });
    } else {
      const { text, indent = 0 } = it;
      out.push({
        text, options: {
          bullet: true, indentLevel: indent, breakLine: i < items.length - 1,
        }
      });
    }
  });
  return out;
}

// Soft section card
function addCard(slide, x, y, w, h, fill = COL.soft) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: fill }, line: { type: "none" },
    shadow: makeShadow(),
  });
}

// Numbered chip (purple circle with number)
function addChip(slide, x, y, n, size = 0.45) {
  slide.addShape(pres.shapes.OVAL, {
    x, y, w: size, h: size,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  slide.addText(String(n), {
    x, y, w: size, h: size,
    fontFace: FONT, fontSize: 14, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });
}

// =========================================================
// SLIDE 0 — Title
// =========================================================
{
  const s = pres.addSlide();
  s.background = { color: COL.uclDeep };

  // Top-left wordmark
  s.addText("UCL  ·  THE BARTLETT", {
    x: 0.7, y: 0.5, w: 6, h: 0.4,
    fontFace: FONT, fontSize: 12, bold: true, color: COL.white,
    charSpacing: 6, margin: 0,
  });

  // Top-right: Waymo logo (white version)
  s.addImage({
    path: A("processed/waymo-logo-white.png"),
    x: W - 2.7, y: 0.45, w: 2.0, h: 0.5,
    sizing: { type: "contain", w: 2.0, h: 0.5 },
  });

  // Thin accent bar (motif) — left of title block
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.55, w: 0.6, h: 0.05,
    fill: { color: COL.ucl }, line: { type: "none" },
  });

  // Pre-title eyebrow
  s.addText("RESEARCH PLAN  ·  2026", {
    x: 0.7, y: 2.1, w: 8, h: 0.4,
    fontFace: FONT, fontSize: 12, bold: true, color: "C8B8D6",
    charSpacing: 4, margin: 0,
  });

  // Main title
  s.addText("Waymo Open Sim Agents\nChallenge", {
    x: 0.7, y: 2.7, w: 11.5, h: 1.9,
    fontFace: FONT, fontSize: 54, bold: true, color: COL.white,
    align: "left", valign: "top", margin: 0,
  });

  // Subtitle
  s.addText("Task understanding and a research-oriented initial plan", {
    x: 0.7, y: 4.6, w: 11.5, h: 0.6,
    fontFace: FONT, fontSize: 22, color: "E0D0EE", align: "left", margin: 0,
  });

  // Tagline
  s.addText("Using WOSAC as a benchmark to study realistic sim-agent design for autonomous driving", {
    x: 0.7, y: 5.2, w: 11.5, h: 0.5,
    fontFace: FONT, fontSize: 14, italic: true, color: COL.rule, margin: 0,
  });

  // Bottom meta line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: H - 1.0, w: 1.5, h: 0.04,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("Supervisor meeting  ·  28 April 2026", {
    x: 0.7, y: H - 0.85, w: 8, h: 0.35,
    fontFace: FONT, fontSize: 11, color: "B89BCB", margin: 0,
  });

  s.addNotes(
    "Today I want to discuss the Waymo Open Sim Agents Challenge. " +
    "My goal is not to chase a leaderboard ranking, but to use WOSAC as a standardised benchmark " +
    "for studying simulation, behaviour modelling and multi-agent interaction in autonomous driving, " +
    "and to find a focused sim-agent design problem worth optimising."
  );
}

// =========================================================
// SLIDE 1 — Motivation
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 1, title: "Motivation: building research foundations for autonomous driving" });

  // Lead paragraph
  s.addText("Why I chose this task", {
    x: 0.6, y: 1.4, w: 12, h: 0.4,
    fontFace: FONT, fontSize: 16, bold: true, color: COL.ink, margin: 0,
  });

  s.addText(
    "Sim agents sit at the intersection of behaviour modelling, motion prediction, multi-agent interaction, " +
    "planning evaluation and safety-critical simulation. WOSAC turns these into a single, well-defined benchmark.",
    {
      x: 0.6, y: 1.85, w: 12, h: 1.0,
      fontFace: FONT, fontSize: 14, color: COL.ink, margin: 0,
    }
  );

  // Five capability chips along a row
  const caps = [
    "Behaviour\nmodelling",
    "Motion\nprediction",
    "Multi-agent\ninteraction",
    "Planning\nevaluation",
    "Safety-critical\nsimulation",
  ];
  const chipW = 2.1, gap = 0.25, total = caps.length * chipW + (caps.length - 1) * gap;
  const startX = (W - total) / 2;
  const chipY = 3.05;

  caps.forEach((label, i) => {
    const x = startX + i * (chipW + gap);
    addCard(s, x, chipY, chipW, 1.2, COL.soft);
    s.addShape(pres.shapes.OVAL, {
      x: x + chipW / 2 - 0.18, y: chipY + 0.18, w: 0.36, h: 0.36,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: x + chipW / 2 - 0.18, y: chipY + 0.18, w: 0.36, h: 0.36,
      fontFace: FONT, fontSize: 12, bold: true, color: COL.white,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(label, {
      x: x + 0.1, y: chipY + 0.6, w: chipW - 0.2, h: 0.6,
      fontFace: FONT, fontSize: 12, bold: true, color: COL.ink,
      align: "center", valign: "middle", margin: 0,
    });
  });

  // Closing assertion (moved up, immediately after chips)
  s.addText(
    "This project treats the challenge as a research platform — not as a competition submission.",
    {
      x: 0.6, y: 4.5, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 14, italic: true, color: COL.ucl, bold: true, margin: 0,
    }
  );

  // ---------- AIMED DELIVERABLES row ----------
  s.addText("WHAT THE PROJECT WILL DELIVER", {
    x: 0.6, y: 5.05, w: 12, h: 0.3,
    fontFace: FONT, fontSize: 10, bold: true, color: COL.muted, margin: 0,
  });

  const dels = [
    { h: "Reproducible pipeline",
      b: "WOMD scenarios → Waymax → 32-rollout submission. Three baselines scored against the official meta-metric." },
    { h: "Focused sim-agent design",
      b: "One model targeting a single capability — closed-loop stability, interaction realism, map adherence, or multimodal generation." },
    { h: "Failure-mode analysis",
      b: "Evidence of what the design improves, where it still fails, and how it compares with simple baselines." },
  ];
  const dy = 5.4, dh = 1.55, dgap = 0.3;
  const dw = (W - 1.2 - dgap * (dels.length - 1)) / dels.length;
  dels.forEach((d, i) => {
    const x = 0.6 + i * (dw + dgap);
    addCard(s, x, dy, dw, dh, COL.white);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: dy, w: 0.10, h: dh,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(`0${i + 1}`, {
      x: x + 0.25, y: dy + 0.18, w: 0.6, h: 0.3,
      fontFace: FONT, fontSize: 10, bold: true, color: COL.ucl, margin: 0,
    });
    s.addText(d.h, {
      x: x + 0.25, y: dy + 0.45, w: dw - 0.4, h: 0.35,
      fontFace: FONT, fontSize: 13, bold: true, color: COL.ink, margin: 0,
    });
    s.addText(d.b, {
      x: x + 0.25, y: dy + 0.85, w: dw - 0.4, h: 0.65,
      fontFace: FONT, fontSize: 11, color: COL.ink, margin: 0,
    });
  });

  s.addNotes(
    "I chose this task because it systematically trains the core capabilities of autonomous driving — " +
    "prediction, simulation, multi-agent interaction, behaviour modelling, planning evaluation. " +
    "The aim is not a high leaderboard rank, but to identify a clear modelling problem in this benchmark " +
    "and improve it in a focused way."
  );
}

// =========================================================
// SLIDE 2 — Background: why realistic simulation matters
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 2, title: "Background: why realistic simulation matters" });

  // Two columns: problem (left) vs role of simulation (right)
  // LEFT card — white with purple side stripe
  addCard(s, 0.6, 1.5, 5.9, 3.8, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.5, w: 0.08, h: 3.8,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("Real-world testing alone is not enough", {
    x: 0.85, y: 1.65, w: 5.5, h: 0.5,
    fontFace: FONT, fontSize: 16, bold: true, color: COL.ucl, margin: 0,
  });
  s.addText(bulletText([
    "expensive to scale",
    "rare or risky scenarios appear infrequently",
    "evaluation feedback is slow and noisy",
    "hard to attribute failures to specific behaviours",
  ]), {
    x: 0.95, y: 2.2, w: 5.4, h: 2.9,
    fontFace: FONT, fontSize: 13, color: COL.ink,
    paraSpaceAfter: 6, margin: 0,
  });

  // RIGHT card — same treatment
  addCard(s, 6.85, 1.5, 5.9, 3.8, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.5, w: 0.08, h: 3.8,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("Simulation provides a scalable alternative", {
    x: 7.1, y: 1.65, w: 5.5, h: 0.5,
    fontFace: FONT, fontSize: 16, bold: true, color: COL.ucl, margin: 0,
  });
  s.addText(bulletText([
    "test rare or risky scenarios at scale",
    "evaluate planning and behaviour models",
    "study multi-agent interactions in closed loop",
    "reduce real-world testing cost",
  ]), {
    x: 7.2, y: 2.2, w: 5.4, h: 2.9,
    fontFace: FONT, fontSize: 13, color: COL.ink,
    paraSpaceAfter: 6, margin: 0,
  });

  // Caveat strip — full width
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 5.5, w: W - 1.2, h: 0.85,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText(
    "Simulation is useful only if the surrounding agents behave realistically.",
    {
      x: 0.85, y: 5.5, w: W - 1.7, h: 0.85,
      fontFace: FONT, fontSize: 14, italic: true, color: COL.white,
      align: "center", valign: "middle", margin: 0,
    }
  );

  // Footer key idea
  s.addText("The key problem is not replaying logs, but generating realistic interactive traffic behaviour.", {
    x: 0.6, y: 6.55, w: 12, h: 0.4,
    fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
  });

  s.addNotes(
    "Autonomous-driving systems are hard to evaluate by real-world driving alone — the cost is high, " +
    "the risk is high, and many edge cases rarely appear. Simulation is therefore essential, but only if " +
    "the surrounding vehicles, pedestrians and cyclists behave realistically. If they do not, the evaluation " +
    "of planning and behaviour models is unreliable."
  );
}

// =========================================================
// SLIDE 3 — Task definition (image-feature; demonstrate.gif on right)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 3, title: "Task: simulating the future traffic world" });

  // LEFT — three labelled blocks (Input → Model → Output)
  // INPUT
  s.addText("INPUT — PAST 1 SECOND", {
    x: 0.6, y: 1.5, w: 6, h: 0.3,
    fontFace: FONT, fontSize: 10, bold: true, color: COL.muted, margin: 0,
  });
  s.addText(bulletText([
    "Vehicle, pedestrian, cyclist states",
    "Autonomous-vehicle (ADV) state",
    "Road map and lane structure",
    "Traffic-light states",
  ]), {
    x: 0.7, y: 1.82, w: 5.7, h: 1.55,
    fontFace: FONT, fontSize: 13, color: COL.ink,
    paraSpaceAfter: 3, margin: 0,
  });

  // MODEL — purple band
  addCard(s, 0.6, 3.5, 5.85, 0.55, COL.ucl);
  s.addText("Sim-agent model", {
    x: 0.6, y: 3.5, w: 5.85, h: 0.55,
    fontFace: FONT, fontSize: 14, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });

  // OUTPUT
  s.addText("OUTPUT — 32 ROLLOUTS × 8 S", {
    x: 0.6, y: 4.2, w: 6, h: 0.3,
    fontFace: FONT, fontSize: 10, bold: true, color: COL.muted, margin: 0,
  });
  s.addText(bulletText([
    "Joint future for all agents (incl. ADV)",
    "Each agent: x, y, z position + heading",
    "32 stochastic rollouts per scenario",
  ]), {
    x: 0.7, y: 4.52, w: 5.7, h: 1.4,
    fontFace: FONT, fontSize: 13, color: COL.ink,
    paraSpaceAfter: 3, margin: 0,
  });

  // RIGHT — demonstrate.gif
  // Original GIF is 480x270 (16:9). Fit into a 6.5"-wide frame.
  const imgW = 6.4, imgH = 6.4 * (270/480);
  const imgX = 6.55, imgY = 1.6;
  // Subtle frame
  s.addShape(pres.shapes.RECTANGLE, {
    x: imgX - 0.06, y: imgY - 0.06, w: imgW + 0.12, h: imgH + 0.12,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addImage({
    path: A("demonstrate.gif"),
    x: imgX, y: imgY, w: imgW, h: imgH,
  });
  s.addText("Example rollout — each box is a simulated agent (position + heading) over 8 s.", {
    x: imgX, y: imgY + imgH + 0.15, w: imgW, h: 0.4,
    fontFace: FONT, fontSize: 10, italic: true, color: COL.muted, margin: 0,
  });

  // Bottom assertion
  s.addText(
    "The model acts as a traffic-world simulator: it generates how the whole scene evolves, not a single trajectory.",
    {
      x: 0.6, y: H - 0.95, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "In plain terms, this task is to train a traffic-world simulator. Given roughly 1 second of real-road history " +
    "— positions, speeds, pedestrians, cyclists, the road map, traffic lights — the model must generate how the " +
    "next 8 seconds of the entire scene evolve. Crucially, it does not generate a single future, but 32 possible " +
    "futures, because the real world is not deterministic. The animation on the right is exactly what a rollout " +
    "looks like: each box is one simulated agent updating its position and heading every step."
  );
}

// =========================================================
// SLIDE 4 — Research framing (competition vs research)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 4, title: "Framing: from competition task to sim-agent design problem" });

  // Lead
  s.addText(
    "I want to use WOSAC as a controlled benchmark, not as a leaderboard target.",
    {
      x: 0.6, y: 1.4, w: 12, h: 0.45,
      fontFace: FONT, fontSize: 16, color: COL.ink, margin: 0,
    }
  );

  // Two contrasting columns
  const cardY = 2.2, cardH = 3.5, gap = 0.4, cardW = (W - 1.2 - gap) / 2;

  // LEFT: competition objective (white card with grey side stripe — secondary)
  addCard(s, 0.6, cardY, cardW, cardH, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: cardY, w: 0.08, h: cardH,
    fill: { color: COL.muted }, line: { type: "none" },
  });
  s.addText("COMPETITION OBJECTIVE", {
    x: 0.85, y: cardY + 0.25, w: cardW - 0.5, h: 0.35,
    fontFace: FONT, fontSize: 11, bold: true, color: COL.muted, margin: 0,
  });
  s.addText("Submit 32 future rollouts per scenario.", {
    x: 0.85, y: cardY + 0.7, w: cardW - 0.5, h: 0.7,
    fontFace: FONT, fontSize: 18, bold: true, color: COL.ink, margin: 0,
  });
  s.addText(bulletText([
    "fixed format and metric",
    "leaderboard ranking",
    "test-set attempts: 3 per 30 days",
  ]), {
    x: 0.95, y: cardY + 1.55, w: cardW - 0.6, h: 1.7,
    fontFace: FONT, fontSize: 13, color: COL.ink,
    paraSpaceAfter: 4, margin: 0,
  });

  // RIGHT: research objective (purple, dominant)
  addCard(s, 0.6 + cardW + gap, cardY, cardW, cardH, COL.ucl);
  s.addText("MY RESEARCH OBJECTIVE", {
    x: 0.85 + cardW + gap, y: cardY + 0.25, w: cardW - 0.5, h: 0.35,
    fontFace: FONT, fontSize: 11, bold: true, color: "E0D0EE", margin: 0,
  });
  s.addText("Identify one modelling weakness and turn it into a strong sim-agent design.", {
    x: 0.85 + cardW + gap, y: cardY + 0.7, w: cardW - 0.5, h: 1.1,
    fontFace: FONT, fontSize: 18, bold: true, color: COL.white, margin: 0,
  });
  s.addText(bulletText([
    "diagnose where baselines fail",
    "isolate one capability to optimise",
    "evaluate what the design improves",
  ]), {
    x: 0.95 + cardW + gap, y: cardY + 1.85, w: cardW - 0.6, h: 1.55,
    fontFace: FONT, fontSize: 13, color: COL.white,
    paraSpaceAfter: 4, margin: 0,
  });

  // Bottom band
  s.addText(
    "WOSAC provides the dataset, simulator, metrics and protocol. My contribution should be a focused model improvement.",
    {
      x: 0.6, y: 6.05, w: 12, h: 0.5,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "This is the point I want to align on with you: I am not framing this project as 'compete in a challenge'. " +
    "It already provides data, simulator, submission format and evaluation. So I want to use it as a research " +
    "platform: pick one specific weakness — closed-loop stability, interaction realism, map adherence — and " +
    "design a better sim agent around that single point."
  );
}

// =========================================================
// SLIDE 5 — Benchmark platform (factorization figure on right)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 5, title: "Benchmark platform: data, simulator, submission" });

  // LEFT — three short blocks
  const lx = 0.6, lw = 6.2;
  const blockH = 1.45;
  const yStart = 1.45;

  function block(i, label, body) {
    const y = yStart + i * (blockH + 0.15);
    addCard(s, lx, y, lw, blockH, COL.soft);
    // small purple square as a marker
    s.addShape(pres.shapes.RECTANGLE, {
      x: lx, y, w: 0.12, h: blockH,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(label, {
      x: lx + 0.3, y: y + 0.15, w: lw - 0.5, h: 0.4,
      fontFace: FONT, fontSize: 13, bold: true, color: COL.ucl, margin: 0,
    });
    s.addText(body, {
      x: lx + 0.3, y: y + 0.55, w: lw - 0.5, h: blockH - 0.65,
      fontFace: FONT, fontSize: 12, color: COL.ink, margin: 0,
    });
  }

  block(0, "Dataset — Waymo Open Motion Dataset",
    "Real-world scenarios: agent trajectories, object types, map features, traffic-light states.");
  block(1, "Simulator — Waymax",
    "Scenario loading, multi-agent rollout interface, baseline agents, submission generation.");
  block(2, "Rollout format",
    "32 rollouts × 8 s (80 steps @ 10 Hz). Position + heading per agent. 150 serialized protos per submission. 3 test-set attempts per 30 days.");

  // RIGHT — factorization figure as the constraint diagram
  const fx = 7.2, fy = 1.45, fw = 5.5;
  s.addText("Required factorization (2025 rule)", {
    x: fx, y: fy, w: fw, h: 0.4,
    fontFace: FONT, fontSize: 14, bold: true, color: COL.ucl, margin: 0,
  });
  // Image
  // Original 1556x563-ish; scale to fit
  s.addImage({
    path: A("processed/factorization.png"),
    x: fx, y: fy + 0.45, w: fw, h: fw * (563/1556),
  });
  // Caption under image
  const capY = fy + 0.45 + fw * (563/1556) + 0.1;
  s.addText(
    "ADV (blue) and world (orange) states must be conditionally independent given the previous joint state. " +
    "Object dimensions are fixed from the final history frame.",
    {
      x: fx, y: capY, w: fw, h: 1.0,
      fontFace: FONT, fontSize: 11, italic: true, color: COL.muted, margin: 0,
    }
  );

  // Bottom strip
  s.addText(
    "A standardised environment for testing whether a sim-agent design improves realism.",
    {
      x: 0.6, y: H - 0.95, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "The benefit of this benchmark is that it is bounded. Data comes from the Waymo Open Motion Dataset; " +
    "simulation and evaluation can be done in Waymax; the submission is a set of trajectory rollouts, not " +
    "model code. So it is effectively a standardised experimental environment. The 2025 challenge also " +
    "requires a specific factorisation: given the previous joint state, the ADV's next state and the world's " +
    "next state must be conditionally independent — the ego cannot 'peek' at the world's next-step output " +
    "within the same step. The figure on the right is Waymo's visualisation of that constraint."
  );
}

// =========================================================
// SLIDE 6 — Evaluation
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 6, title: "Evaluation: distribution matching, not trajectory error" });

  // Lead
  s.addText(
    "WOSAC scores submissions as a distribution-matching problem: the simulated rollout distribution is compared with the real-world distribution.",
    {
      x: 0.6, y: 1.4, w: 12, h: 0.7,
      fontFace: FONT, fontSize: 14, color: COL.ink, margin: 0,
    }
  );

  // Three columns of metric families
  const cardY = 2.4, cardH = 3.0, gap = 0.3, ncards = 3;
  const cardW = (W - 1.2 - (ncards - 1) * gap) / ncards;

  function metricCard(i, head, lines) {
    const x = 0.6 + i * (cardW + gap);
    addCard(s, x, cardY, cardW, cardH, COL.white);
    // top accent
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: 0.18,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(head, {
      x: x + 0.25, y: cardY + 0.3, w: cardW - 0.5, h: 0.5,
      fontFace: FONT, fontSize: 15, bold: true, color: COL.ucl, margin: 0,
    });
    s.addText(bulletText(lines), {
      x: x + 0.25, y: cardY + 0.85, w: cardW - 0.5, h: cardH - 1.0,
      fontFace: FONT, fontSize: 12, color: COL.ink,
      paraSpaceAfter: 4, margin: 0,
    });
  }

  metricCard(0, "Motion realism (kinematic)", [
    "linear speed + acceleration",
    "angular speed + acceleration",
    "2025: smoother estimation",
  ]);
  metricCard(1, "Interaction realism", [
    "collision (capsule shape — 2025)",
    "distance to nearest object",
    "time-to-collision (vehicles; new filter)",
  ]);
  metricCard(2, "Map adherence", [
    "off-road behaviour",
    "distance to road edges",
    "traffic-light violation (2025: NEW)",
  ]);

  // Aggregation strip
  addCard(s, 0.6, 5.6, W - 1.2, 1.0, COL.soft);
  s.addText(
    "per-feature negative log-likelihood   →   weighted-mean meta-metric   →   higher = more realistic",
    {
      x: 0.85, y: 5.7, w: W - 1.7, h: 0.8,
      fontFace: FONT, fontSize: 14, bold: true, color: COL.ucl,
      align: "center", valign: "middle", margin: 0, charSpacing: 1,
    }
  );

  // Bottom note (kept above footer)
  s.addText(
    "2025 metric updates mean older leaderboard scores are not directly comparable.",
    {
      x: 0.6, y: 6.75, w: 12, h: 0.3,
      fontFace: FONT, fontSize: 11, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "This is not standard trajectory prediction. The model produces 32 futures, those form a simulated " +
    "behaviour distribution, and the score asks how well that distribution matches the real-driving " +
    "distribution. So these metrics also work as diagnostics: they tell me which aspect of the rollout is " +
    "unrealistic. The 2025 version updated several metrics — capsule-shape collisions, a new traffic-light " +
    "violation metric, a TTC filter and smoother kinematic estimation — so older baseline numbers are not " +
    "directly comparable."
  );
}

// =========================================================
// SLIDE 7 — Candidate optimization points (2x2 grid)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 7, title: "Candidate optimisation points" });

  s.addText(
    "Four directions where baseline sim agents typically fail — the project should pick one.",
    {
      x: 0.6, y: 1.3, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 13, italic: true, color: COL.muted, margin: 0,
    }
  );

  const dirs = [
    { letter: "A", title: "Closed-loop stability",
      problem: "Small one-step errors accumulate over 80 steps.",
      focus: "Train a model that stays stable during long autoregressive rollout." },
    { letter: "B", title: "Interaction realism",
      problem: "Independent prediction causes collisions or unrealistic yielding.",
      focus: "Agent–agent attention or graph-based interaction modelling." },
    { letter: "C", title: "Map adherence",
      problem: "Agents drift off-road or violate lane / traffic constraints.",
      focus: "Map-conditioned decoding or constraint-aware rollout." },
    { letter: "D", title: "Multimodal generation",
      problem: "One deterministic future cannot represent real-world uncertainty.",
      focus: "Latent / mixture / token-based sampling for diverse rollouts." },
  ];

  const gx = 0.6, gy = 1.85, gw = (W - 1.2 - 0.3) / 2, gh = 2.45;
  const rowGap = 0.20;

  dirs.forEach((d, i) => {
    const r = Math.floor(i / 2), c = i % 2;
    const x = gx + c * (gw + 0.3), y = gy + r * (gh + rowGap);
    addCard(s, x, y, gw, gh, COL.white);
    // letter chip top-left
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.3, y: y + 0.3, w: 0.65, h: 0.65,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(d.letter, {
      x: x + 0.3, y: y + 0.3, w: 0.65, h: 0.65,
      fontFace: FONT, fontSize: 20, bold: true, color: COL.white,
      align: "center", valign: "middle", margin: 0,
    });
    // Title beside chip
    s.addText(d.title, {
      x: x + 1.05, y: y + 0.32, w: gw - 1.3, h: 0.6,
      fontFace: FONT, fontSize: 17, bold: true, color: COL.ucl,
      valign: "middle", margin: 0,
    });
    // Problem block
    s.addText("PROBLEM", {
      x: x + 0.3, y: y + 1.05, w: gw - 0.6, h: 0.25,
      fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
    });
    s.addText(d.problem, {
      x: x + 0.3, y: y + 1.30, w: gw - 0.6, h: 0.55,
      fontFace: FONT, fontSize: 12, color: COL.ink, margin: 0,
    });
    // Focus block
    s.addText("POSSIBLE FOCUS", {
      x: x + 0.3, y: y + 1.85, w: gw - 0.6, h: 0.25,
      fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
    });
    s.addText(d.focus, {
      x: x + 0.3, y: y + 2.10, w: gw - 0.6, h: 0.32,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.ucl, margin: 0,
    });
  });

  s.addNotes(
    "I do not want to start with one big complex model. The more reasonable path is to run the benchmark, " +
    "diagnose where baselines fail, then pick the most worthwhile direction — closed-loop stability, " +
    "interaction realism, map adherence or multimodal generation — so the project's contribution is sharp."
  );
}

// =========================================================
// SLIDE 8 — Proposed initial focus
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 8, title: "Proposed initial focus: stable, interaction-aware sim agents" });

  // Big hypothesis statement
  addCard(s, 0.6, 1.4, W - 1.2, 1.4, COL.ucl);
  s.addText(
    "A good sim agent must remain stable and socially plausible across an 80-step closed-loop rollout — not just predict the next position accurately.",
    {
      x: 0.9, y: 1.55, w: W - 1.8, h: 1.1,
      fontFace: FONT, fontSize: 18, bold: true, color: COL.white,
      valign: "middle", margin: 0,
    }
  );

  // Components row
  const items = [
    "Autoregressive sim-agent model",
    "Agent–agent interaction encoding",
    "Map-conditioned state update",
    "Loss terms: collision · off-road · smoothness",
  ];
  const ix = 0.6, iy = 3.2, iw = (W - 1.2 - 0.3 * (items.length - 1)) / items.length, ih = 1.7;
  items.forEach((t, i) => {
    const x = ix + i * (iw + 0.3);
    addCard(s, x, iy, iw, ih, COL.soft);
    addChip(s, x + 0.25, iy + 0.25, i + 1, 0.45);
    s.addText(t, {
      x: x + 0.25, y: iy + 0.85, w: iw - 0.5, h: 0.8,
      fontFace: FONT, fontSize: 14, bold: true, color: COL.ink, margin: 0,
    });
  });

  // Closing
  s.addText("First research goal", {
    x: 0.6, y: 5.4, w: 12, h: 0.35,
    fontFace: FONT, fontSize: 11, bold: true, color: COL.muted, charSpacing: 2, margin: 0,
  });
  s.addText(
    "Design a sim agent that improves closed-loop realism — not just open-loop prediction accuracy.",
    {
      x: 0.6, y: 5.7, w: 12, h: 0.6,
      fontFace: FONT, fontSize: 16, italic: true, color: COL.ucl, bold: true, margin: 0,
    }
  );

  s.addNotes(
    "I lean towards starting on closed-loop stability and interaction realism, because the essence of a sim " +
    "agent is not whether the next step is accurate, but whether 80-step rollouts stay stable, plausible, " +
    "non-colliding, on-road, and socially realistic between agents."
  );
}

// =========================================================
// SLIDE 9 — Roadmap (timeline)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 9, title: "Proposed roadmap" });

  s.addText("Diagnosis-driven: understand failures first, then design a focused improvement.", {
    x: 0.6, y: 1.35, w: 12, h: 0.4,
    fontFace: FONT, fontSize: 14, color: COL.ink, margin: 0,
  });

  const stages = [
    "Understand data, metrics, rollout format",
    "Reproduce Waymax baseline pipeline",
    "Diagnose baseline failure modes",
    "Select one research focus",
    "Design improved sim-agent model",
    "Compare against simple baselines",
    "Analyse improvements and limitations",
  ];

  const tx = 0.9, ty = 2.3, tw = W - 1.8;
  // horizontal connector line
  s.addShape(pres.shapes.RECTANGLE, {
    x: tx + 0.25, y: ty + 0.45, w: tw - 0.5, h: 0.04,
    fill: { color: COL.rule }, line: { type: "none" },
  });

  const n = stages.length;
  const step = (tw - 0.5) / (n - 1);
  stages.forEach((label, i) => {
    const cx = tx + 0.25 + i * step;
    // dot
    s.addShape(pres.shapes.OVAL, {
      x: cx - 0.18, y: ty + 0.29, w: 0.36, h: 0.36,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: cx - 0.18, y: ty + 0.29, w: 0.36, h: 0.36,
      fontFace: FONT, fontSize: 11, bold: true, color: COL.white,
      align: "center", valign: "middle", margin: 0,
    });
    // label below (alternating up/down would crowd — keep below)
    s.addText(label, {
      x: cx - 0.85, y: ty + 0.85, w: 1.7, h: 1.4,
      fontFace: FONT, fontSize: 11, color: COL.ink,
      align: "center", valign: "top", margin: 0,
    });
  });

  // Bottom — three phase cards with rough timeframes
  const phY = 4.7, phH = 1.85, phGap = 0.30;
  const phW = (W - 1.2 - phGap * 2) / 3;
  const phases = [
    {
      tag: "PHASE 1",
      time: "weeks 1–3",
      title: "Reproduce + diagnose",
      stages: "Stages 1–3",
      detail: "Understand data, run Waymax tutorial, score three baselines, characterise failure modes.",
    },
    {
      tag: "PHASE 2",
      time: "weeks 4–7",
      title: "Focused model design",
      stages: "Stages 4–5",
      detail: "Pick one capability, build a sim-agent model around it (encoder, interaction, decoder, losses).",
    },
    {
      tag: "PHASE 3",
      time: "weeks 8–10",
      title: "Evaluate + analyse",
      stages: "Stages 6–7",
      detail: "Compare against baselines, analyse where the design improves and where it still fails.",
    },
  ];
  phases.forEach((p, i) => {
    const x = 0.6 + i * (phW + phGap);
    addCard(s, x, phY, phW, phH, COL.white);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: phY, w: phW, h: 0.45,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(p.tag, {
      x: x + 0.2, y: phY, w: phW - 0.4, h: 0.45,
      fontFace: FONT, fontSize: 11, bold: true, color: COL.white,
      valign: "middle", margin: 0, charSpacing: 2,
    });
    s.addText(p.time, {
      x: x + 0.2, y: phY, w: phW - 0.4, h: 0.45,
      fontFace: FONT, fontSize: 11, italic: true, color: "E0D0EE",
      align: "right", valign: "middle", margin: 0,
    });
    s.addText(p.title, {
      x: x + 0.2, y: phY + 0.55, w: phW - 0.4, h: 0.4,
      fontFace: FONT, fontSize: 14, bold: true, color: COL.ucl, margin: 0,
    });
    s.addText(p.stages, {
      x: x + 0.2, y: phY + 0.95, w: phW - 0.4, h: 0.3,
      fontFace: FONT, fontSize: 10, color: COL.muted, margin: 0,
    });
    s.addText(p.detail, {
      x: x + 0.2, y: phY + 1.25, w: phW - 0.4, h: 0.55,
      fontFace: FONT, fontSize: 11, color: COL.ink, margin: 0,
    });
  });

  s.addNotes(
    "I do not want to jump straight to a complex model. A safer route is to understand the data and metrics, " +
    "reproduce the Waymax pipeline, then use simple baselines to expose where the failures are — off-road? " +
    "collisions? unstable rollouts? Once those are clear, pick one specific direction for the model design."
  );
}

// =========================================================
// SLIDE 10 — Phase 1A: Steps 1–2 (understand data + run tutorial)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 10, title: "Phase 1A · Steps 1–2: understand the data, run the official tutorial" });

  // Two columns: Step 1 vs Step 2
  const ctop = 1.45, ch = 4.85, cgap = 0.35, cw = (W - 1.2 - cgap) / 2;

  // ---------- LEFT: Step 1 — understand the data ----------
  addCard(s, 0.6, ctop, cw, ch, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: ctop, w: 0.12, h: ch,
    fill: { color: COL.ucl }, line: { type: "none" },
  });

  // Step badge
  s.addShape(pres.shapes.OVAL, {
    x: 0.85, y: ctop + 0.25, w: 0.5, h: 0.5,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("1", {
    x: 0.85, y: ctop + 0.25, w: 0.5, h: 0.5,
    fontFace: FONT, fontSize: 18, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("Understand the data and task format", {
    x: 1.45, y: ctop + 0.27, w: cw - 1.0, h: 0.5,
    fontFace: FONT, fontSize: 15, bold: true, color: COL.ucl,
    valign: "middle", margin: 0,
  });

  // Dataset facts strip
  s.addText("DATASET — WAYMO OPEN MOTION DATASET v1.2.0", {
    x: 0.95, y: ctop + 0.95, w: cw - 0.5, h: 0.3,
    fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
  });
  s.addText(bulletText([
    "9.1 s scenario @ 10 Hz  →  ~1.1 s history + 8 s future",
    "Future = 80 simulation steps",
    "Up to 128 agents per scenario; 1 is the AV / ADV",
    "Object types: vehicle · pedestrian · cyclist",
    "Per scenario: trajectories, current state, map, traffic lights",
  ]), {
    x: 1.05, y: ctop + 1.25, w: cw - 0.55, h: 2.1,
    fontFace: FONT, fontSize: 12, color: COL.ink, paraSpaceAfter: 4, margin: 0,
  });

  // First-week target callout
  addCard(s, 0.95, ctop + 3.45, cw - 0.45, 1.20, COL.soft);
  s.addText("FIRST-WEEK TARGET", {
    x: 1.10, y: ctop + 3.55, w: cw - 0.75, h: 0.25,
    fontFace: FONT, fontSize: 9, bold: true, color: COL.ucl, margin: 0,
  });
  s.addText("Read one scenario and visualise it: past trajectories, lanes, agents, current frame.", {
    x: 1.10, y: ctop + 3.80, w: cw - 0.75, h: 0.80,
    fontFace: FONT, fontSize: 11, italic: true, color: COL.ink, margin: 0,
  });

  // ---------- RIGHT: Step 2 — run the official tutorial ----------
  const rx = 0.6 + cw + cgap;
  addCard(s, rx, ctop, cw, ch, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: ctop, w: 0.12, h: ch,
    fill: { color: COL.ucl }, line: { type: "none" },
  });

  s.addShape(pres.shapes.OVAL, {
    x: rx + 0.25, y: ctop + 0.25, w: 0.5, h: 0.5,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("2", {
    x: rx + 0.25, y: ctop + 0.25, w: 0.5, h: 0.5,
    fontFace: FONT, fontSize: 18, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("Run the official Waymax tutorial → first valid submission", {
    x: rx + 0.85, y: ctop + 0.27, w: cw - 1.0, h: 0.5,
    fontFace: FONT, fontSize: 15, bold: true, color: COL.ucl,
    valign: "middle", margin: 0,
  });

  // Tutorial responsibilities
  s.addText("THE TUTORIAL HANDLES", {
    x: rx + 0.35, y: ctop + 0.95, w: cw - 0.5, h: 0.3,
    fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
  });
  s.addText(bulletText([
    "Scenario id and Waymax dataloader",
    "Proto format and binary sharding",
    "SimAgentsChallengeSubmission packaging",
  ]), {
    x: rx + 0.45, y: ctop + 1.25, w: cw - 0.55, h: 1.25,
    fontFace: FONT, fontSize: 12, color: COL.ink, paraSpaceAfter: 4, margin: 0,
  });

  // Output specification
  s.addText("OUTPUT PER SCENARIO", {
    x: rx + 0.35, y: ctop + 2.55, w: cw - 0.5, h: 0.3,
    fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
  });
  s.addText(bulletText([
    "32 rollouts × 80 steps × all valid agents",
    "(x, y, z, heading) per (agent, step)",
  ]), {
    x: rx + 0.45, y: ctop + 2.85, w: cw - 0.55, h: 0.95,
    fontFace: FONT, fontSize: 12, color: COL.ink, paraSpaceAfter: 4, margin: 0,
  });

  // Final artefact pill
  addCard(s, rx + 0.35, ctop + 3.85, cw - 0.55, 0.80, COL.ucl);
  s.addText("Final artefact:  150 protos  ·  .tar.gz  ·  legal submission", {
    x: rx + 0.45, y: ctop + 3.85, w: cw - 0.75, h: 0.80,
    fontFace: FONT, fontSize: 12, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });

  // Bottom
  s.addText(
    "Goal of Phase 1A — a working pipeline that produces a legal submission, not a high score.",
    {
      x: 0.6, y: 6.55, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "Phase 1A has two steps. Step 1 is to understand the data and the task format. WOMD v1.2.0 scenarios are " +
    "9.1 seconds at 10 Hz — about 1.1 s history plus 8 s future, which is 80 simulation steps. Each scenario " +
    "has up to 128 agents with one ADV. The goal here is not to train, just to read and visualise one scenario. " +
    "Step 2 is to run the official Waymax tutorial end-to-end with a baseline agent like constant-velocity, " +
    "and produce a legal SimAgentsChallengeSubmission. Score does not matter yet — pipeline correctness does."
  );
}

// =========================================================
// SLIDE 11 — Phase 1B: Steps 3–4 (three baselines + first learned model)
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 11, title: "Phase 1B · Steps 3–4: three baselines + first learned model" });

  // Two columns
  const ctop = 1.45, ch = 4.85, cgap = 0.35, cw = (W - 1.2 - cgap) / 2;

  // ---------- LEFT: Step 3 — three baselines ----------
  addCard(s, 0.6, ctop, cw, ch, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: ctop, w: 0.12, h: ch,
    fill: { color: COL.ucl }, line: { type: "none" },
  });

  s.addShape(pres.shapes.OVAL, {
    x: 0.85, y: ctop + 0.25, w: 0.5, h: 0.5,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("3", {
    x: 0.85, y: ctop + 0.25, w: 0.5, h: 0.5,
    fontFace: FONT, fontSize: 18, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("Three simple baselines", {
    x: 1.45, y: ctop + 0.27, w: cw - 1.0, h: 0.5,
    fontFace: FONT, fontSize: 15, bold: true, color: COL.ucl,
    valign: "middle", margin: 0,
  });

  // Three baseline rows
  const baselines = [
    { name: "Log replay", body: "Copy the recorded future. Sanity-checks pipeline; invalid for the test set." },
    { name: "Constant velocity", body: "Each agent extrapolates current speed in a straight line." },
    { name: "Simple interaction rules", body: "Lane-keep + brake on lead car; basic ped/cyclist motion." },
  ];
  const bly = ctop + 0.95;
  baselines.forEach((b, i) => {
    const y = bly + i * 0.95;
    // small numbered dot
    s.addShape(pres.shapes.OVAL, {
      x: 0.95, y: y + 0.05, w: 0.3, h: 0.3,
      fill: { color: COL.soft }, line: { type: "none" },
    });
    s.addText(String.fromCharCode(65 + i), { // A, B, C
      x: 0.95, y: y + 0.05, w: 0.3, h: 0.3,
      fontFace: FONT, fontSize: 11, bold: true, color: COL.ucl,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(b.name, {
      x: 1.35, y: y, w: cw - 0.85, h: 0.35,
      fontFace: FONT, fontSize: 13, bold: true, color: COL.ucl, margin: 0,
    });
    s.addText(b.body, {
      x: 1.35, y: y + 0.35, w: cw - 0.85, h: 0.50,
      fontFace: FONT, fontSize: 11, color: COL.ink, margin: 0,
    });
  });

  // Insight callout
  addCard(s, 0.95, ctop + 3.95, cw - 0.45, 0.80, COL.soft);
  s.addText("Purpose: not to win — to read the metric (e.g. const-vel is fine on motion, fails on off-road / red light).", {
    x: 1.10, y: ctop + 3.95, w: cw - 0.75, h: 0.80,
    fontFace: FONT, fontSize: 11, italic: true, color: COL.ink,
    valign: "middle", margin: 0,
  });

  // ---------- RIGHT: Step 4 — first learned model ----------
  const rx = 0.6 + cw + cgap;
  addCard(s, rx, ctop, cw, ch, COL.white);
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: ctop, w: 0.12, h: ch,
    fill: { color: COL.ucl }, line: { type: "none" },
  });

  s.addShape(pres.shapes.OVAL, {
    x: rx + 0.25, y: ctop + 0.25, w: 0.5, h: 0.5,
    fill: { color: COL.ucl }, line: { type: "none" },
  });
  s.addText("4", {
    x: rx + 0.25, y: ctop + 0.25, w: 0.5, h: 0.5,
    fontFace: FONT, fontSize: 18, bold: true, color: COL.white,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText("First learned model", {
    x: rx + 0.85, y: ctop + 0.27, w: cw - 1.0, h: 0.5,
    fontFace: FONT, fontSize: 15, bold: true, color: COL.ucl,
    valign: "middle", margin: 0,
  });

  // Input
  s.addText("INPUT", {
    x: rx + 0.35, y: ctop + 0.95, w: cw - 0.5, h: 0.3,
    fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
  });
  s.addText(bulletText([
    "past 1 s agent states",
    "vector map features",
    "agent type + relative positions",
    "traffic-light state",
  ]), {
    x: rx + 0.45, y: ctop + 1.20, w: cw - 0.55, h: 1.55,
    fontFace: FONT, fontSize: 12, color: COL.ink, paraSpaceAfter: 3, margin: 0,
  });

  // Output
  s.addText("OUTPUT  →  next-step Δx, Δy, Δheading", {
    x: rx + 0.35, y: ctop + 2.80, w: cw - 0.5, h: 0.3,
    fontFace: FONT, fontSize: 11, bold: true, color: COL.ucl, margin: 0,
  });

  // Rollout loop pseudo-code (extended card, comfortable bottom padding)
  addCard(s, rx + 0.35, ctop + 3.20, cw - 0.55, 1.55, COL.soft);
  s.addText("ROLLOUT — REPEAT 80 TIMES", {
    x: rx + 0.50, y: ctop + 3.30, w: cw - 0.85, h: 0.25,
    fontFace: FONT, fontSize: 9, bold: true, color: COL.muted, margin: 0,
  });
  s.addText([
    { text: "observe simulated scene\n", options: { breakLine: true } },
    { text: "predict ADV next state         ", options: { color: COL.ucl } },
    { text: "(independent of world per\n", options: { color: COL.muted, italic: true, breakLine: true } },
    { text: "predict world next state          ", options: { color: COL.ucl } },
    { text: "WOSAC factorisation rule)\n", options: { color: COL.muted, italic: true, breakLine: true } },
    { text: "update scene", options: {} },
  ], {
    x: rx + 0.50, y: ctop + 3.55, w: cw - 0.85, h: 1.10,
    fontFace: "Consolas", fontSize: 10, color: COL.ink, margin: 0,
  });

  // Bottom
  s.addText(
    "By end of Phase 1: working pipeline · 3 baselines scored · 1 learned model trained · failure modes characterised.",
    {
      x: 0.6, y: 6.55, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "Phase 1B has two steps. Step 3 is to run three simple baselines: log replay (copies the real future, " +
    "valid only on training/validation), constant velocity, and a simple interaction rule that keeps lane and " +
    "brakes on lead vehicles. The point is not to win — it is to read the WOSAC metric: which failure modes " +
    "does each baseline trigger? Step 4 is the first learned model: take a trajectory-prediction model, give " +
    "it past 1 s agent states, vector map features, agent type, relative positions and traffic-light state, " +
    "and predict next-step Δx, Δy, Δheading. Train autoregressively; at rollout time loop 80 steps, predicting " +
    "ADV and world states separately to honour the WOSAC conditional-independence factorisation."
  );
}

// =========================================================
// SLIDE 12 — Phase 2: single-agent prediction → joint multi-agent simulation
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 12, title: "Phase 2: from single-agent prediction to joint multi-agent simulation" });

  // Lead — Step 5 framing
  addCard(s, 0.6, 1.4, W - 1.2, 0.95, COL.ucl);
  s.addText(
    "The hard part is not predicting one car — it is making all agents jointly plausible.",
    {
      x: 0.85, y: 1.5, w: W - 1.7, h: 0.8,
      fontFace: FONT, fontSize: 16, bold: true, color: COL.white,
      align: "center", valign: "middle", margin: 0,
    }
  );

  // Six interaction-realism dimensions
  const dims = [
    "Agent–agent\ninteraction",
    "Vehicle ↔ pedestrian\nyielding",
    "Car following",
    "Lane keeping",
    "Traffic-light\ncompliance",
    "Multimodal\nfutures",
  ];
  const dy0 = 2.55, dh = 1.05;
  const dn = dims.length;
  const dgap = 0.18;
  const dw = (W - 1.2 - (dn - 1) * dgap) / dn;
  dims.forEach((label, i) => {
    const x = 0.6 + i * (dw + dgap);
    addCard(s, x, dy0, dw, dh, COL.soft);
    s.addText(label, {
      x: x + 0.1, y: dy0 + 0.1, w: dw - 0.2, h: dh - 0.2,
      fontFace: FONT, fontSize: 11, bold: true, color: COL.ucl,
      align: "center", valign: "middle", margin: 0,
    });
  });

  // Architecture flow (compact)
  const ay = 4.0;
  const flow = [
    "Vectorized\nmap encoder",
    "Agent history\nencoder",
    "Agent–agent\nattention / GNN",
    "Stochastic\ndecoder",
    "Constraint-aware\npost-processing",
  ];
  const fgap = 0.12, fw = (W - 1.2 - (flow.length - 1) * (fgap + 0.3)) / flow.length;
  let fx = 0.6;
  flow.forEach((label, i) => {
    const isCore = (i === 2);   // emphasize agent-agent module
    addCard(s, fx, ay, fw, 1.4, isCore ? COL.ucl : COL.white);
    // Top accent bar only on white boxes — solid purple core needs no accent
    if (!isCore) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: fx, y: ay, w: fw, h: 0.10,
        fill: { color: COL.ucl }, line: { type: "none" },
      });
    }
    s.addText(label, {
      x: fx + 0.1, y: ay + 0.2, w: fw - 0.2, h: 1.1,
      fontFace: FONT, fontSize: 12, bold: true,
      color: isCore ? COL.white : COL.ucl,
      align: "center", valign: "middle", margin: 0,
    });
    if (i < flow.length - 1) {
      s.addShape(pres.shapes.LINE, {
        x: fx + fw + 0.02, y: ay + 0.7, w: 0.26, h: 0,
        line: { color: COL.ucl, width: 2, endArrowType: "triangle" },
      });
    }
    fx += fw + 0.30;
  });

  // Loop annotation
  s.addText("autoregressive loop  ·  repeat × 80 steps", {
    x: 0.6, y: 5.5, w: W - 1.2, h: 0.35,
    fontFace: FONT, fontSize: 11, italic: true, color: COL.muted,
    align: "center", margin: 0,
  });

  // Independent prediction caveat
  addCard(s, 0.6, 5.95, W - 1.2, 0.7, COL.soft);
  s.addText(
    "Independent per-agent prediction often produces collisions — the agent–agent module exists to fix this.",
    {
      x: 0.85, y: 5.95, w: W - 1.7, h: 0.7,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.ink,
      align: "center", valign: "middle", margin: 0,
    }
  );

  // Bottom
  s.addText(
    "Success = a clear improvement on one capability with interpretable gains, not a top leaderboard score.",
    {
      x: 0.6, y: 6.75, w: 12, h: 0.3,
      fontFace: FONT, fontSize: 11, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "Phase 2's central insight is that a sim agent is not a one-car predictor — it has to make every agent " +
    "in the scene jointly plausible. If each agent is decoded independently, two cars will collide, no one " +
    "will yield, and red lights get ignored. That is why the model recipe puts an agent–agent attention or " +
    "GNN module between the encoders and the decoder, and why constraint-aware post-processing matters. The " +
    "WOSAC paper itself states that sim agents must be realistic and interactive — log replay or simple rules " +
    "are not enough."
  );
}

// =========================================================
// SLIDE 12 — Phase 3: evaluate the design
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 13, title: "Phase 3: evaluate the design, not only the score" });

  // Three columns: baselines / dimensions / key question
  const cy = 1.5, ch = 4.5, gap = 0.35, ncols = 3;
  const cw = (W - 1.2 - gap * (ncols - 1)) / ncols;

  function panel(i, head, content, fillTitle = COL.ucl) {
    const x = 0.6 + i * (cw + gap);
    addCard(s, x, cy, cw, ch, COL.white);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: cy, w: cw, h: 0.6,
      fill: { color: fillTitle }, line: { type: "none" },
    });
    s.addText(head, {
      x: x + 0.25, y: cy, w: cw - 0.5, h: 0.6,
      fontFace: FONT, fontSize: 14, bold: true, color: COL.white,
      valign: "middle", charSpacing: 2, margin: 0,
    });
    s.addText(content, {
      x: x + 0.3, y: cy + 0.85, w: cw - 0.6, h: ch - 1.0,
      fontFace: FONT, fontSize: 13, color: COL.ink,
      paraSpaceAfter: 6, margin: 0,
    });
  }

  panel(0, "Baselines to compare", bulletText([
    "Constant-velocity",
    "Simple rule-based",
    "Initial learned baseline",
  ]));
  panel(1, "Dimensions to analyse", bulletText([
    "Motion realism",
    "Interaction realism",
    "Map adherence",
    "Closed-loop stability",
    "Diversity across 32 rollouts",
  ]));
  panel(2, "Key research question", bulletText([
    "Which failure mode does the design reduce most clearly?",
    "Does the gain hold across scenario types?",
    "Where does it still fail?",
  ]));

  // Bottom statement
  addCard(s, 0.6, H - 1.5, W - 1.2, 0.8, COL.soft);
  s.addText(
    "The final result should explain why the model works, where it improves, and where it still fails.",
    {
      x: 0.85, y: H - 1.45, w: W - 1.7, h: 0.7,
      fontFace: FONT, fontSize: 14, italic: true, color: COL.ucl, bold: true,
      align: "center", valign: "middle", margin: 0,
    }
  );

  s.addNotes(
    "Evaluation should not be a single aggregate score. The harder question is: what specifically did this " +
    "design improve? Fewer collisions? Less off-road? More stable 80-step rollouts? More plausible diversity " +
    "across the 32 rollouts? That kind of analysis is what makes this a research project rather than a contest."
  );
}

// =========================================================
// SLIDE 13 — Discussion questions
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 14, title: "Discussion questions" });

  const qs = [
    "Is this a suitable benchmark for building autonomous-driving research foundations?",
    "Which research focus is most valuable: closed-loop stability, interaction realism, map adherence, or multimodal generation?",
    "Should I start with rule-based diagnosis or a small learned baseline?",
    "What would a convincing 4–6 week milestone look like?",
    "What kind of final output would be most useful — pipeline, model, failure-mode analysis, technical report?",
  ];

  const qy0 = 1.45, qH = 0.78, qGap = 0.12;
  qs.forEach((q, i) => {
    const y = qy0 + i * (qH + qGap);
    addCard(s, 0.6, y, W - 1.2, qH, COL.white);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y, w: 0.12, h: qH,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(`Q${i + 1}`, {
      x: 0.85, y, w: 0.55, h: qH,
      fontFace: FONT, fontSize: 13, bold: true, color: COL.ucl,
      valign: "middle", margin: 0,
    });
    s.addText(q, {
      x: 1.40, y, w: W - 1.2 - 0.85, h: qH,
      fontFace: FONT, fontSize: 13, color: COL.ink,
      valign: "middle", margin: 0,
    });
  });

  // Closing italic placed safely above footer
  s.addText(
    "Goal of this meeting — align on scope, focus, and the first milestone.",
    {
      x: 0.6, y: 6.45, w: 12, h: 0.35,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  s.addNotes(
    "What I hope this meeting yields is not a yes/no on 'should I enter the competition'. It is alignment " +
    "on whether this benchmark is the right research vehicle, and which specific direction to optimise first."
  );
}

// =========================================================
// SLIDE 14 — References
// =========================================================
{
  const s = pres.addSlide();
  addChrome(s, { pageNum: 15, title: "References" });

  const refs = [
    "Montali et al. — The Waymo Open Sim Agents Challenge.",
    "Gulino et al. — Waymax: An Accelerated, Data-Driven Simulator for Large-Scale Autonomous Driving Research.",
    "Waymo Open Dataset 2025 Sim Agents Challenge — waymo.com/open/challenges/2025/sim-agents/",
    "Waymax WOSAC submission tutorial (official GitHub).",
    "Waymo Open Dataset Sim Agents tutorial.",
    "Recent WOSAC 2024–2025 technical reports.",
  ];

  refs.forEach((r, i) => {
    const y = 1.5 + i * 0.55;
    // numbered chip — matches the visual language of other slides
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: y + 0.08, w: 0.35, h: 0.35,
      fill: { color: COL.ucl }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: 0.6, y: y + 0.08, w: 0.35, h: 0.35,
      fontFace: FONT, fontSize: 11, bold: true, color: COL.white,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(r, {
      x: 1.10, y, w: W - 1.7, h: 0.5,
      fontFace: FONT, fontSize: 13, color: COL.ink, valign: "middle", margin: 0,
    });
  });

  // Closing italic — matches other slides' rhythm
  s.addText(
    "These are the materials I will read and reproduce; their content is folded into the earlier slides.",
    {
      x: 0.6, y: 5.2, w: 12, h: 0.4,
      fontFace: FONT, fontSize: 12, italic: true, color: COL.muted, margin: 0,
    }
  );

  // Waymo logo (purple) bottom-right
  s.addImage({
    path: A("processed/waymo-logo-purple.png"),
    x: W - 2.7, y: H - 1.2, w: 1.9, h: 0.45,
    sizing: { type: "contain", w: 1.9, h: 0.45 },
  });

  s.addNotes(
    "These are the materials I will read and reproduce. The presentation has folded their content into the " +
    "earlier slides rather than dedicating a slide per paper."
  );
}

// =========================================================
// Write file
// =========================================================
pres.writeFile({ fileName: path.join(DIST, "WOSAC_Research_Plan.pptx") })
  .then(name => console.log("Wrote " + name));
